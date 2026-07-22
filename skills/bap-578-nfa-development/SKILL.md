---
id: bap-578-nfa-development
name: BAP-578 NFA Development
description: Build Non-Fungible Agents (NFAs) on BNB Chain using the BAP-578 standard. Covers core interface, agent lifecycle, metadata, funding, learning modules, vault permissions, security patterns, and deployment.
category: Blockchain
author: saiboyizhan
version: 2.0.0
tags:
  - bap-578
  - nfa
  - bnb-chain
  - solidity
  - erc-721
  - ai-agent
requires:
  - "solidity>=0.8.20"
  - "hardhat"
  - "@openzeppelin/contracts-upgradeable"
  - "@openzeppelin/hardhat-upgrades"
examples:
  - "How do I create an NFA contract using BAP-578?"
  - "What is the difference between BAP-578 and ERC-721?"
  - "Help me deploy an NFA agent on BNB Chain"
  - "How does agent funding and withdrawal work in BAP-578?"
  - "How do vault permissions work in BAP-578?"
  - "How do I enable learning (Merkle root) for an NFA?"
---

# BAP-578 NFA Development

Guide for building Non-Fungible Agents (NFAs) on BNB Chain using the BAP-578 standard — the first BNB Chain Application Proposal for on-chain AI agents.

## What is BAP-578?

BAP-578 is a token standard that extends ERC-721 to support autonomous AI agents as on-chain assets. Unlike static NFTs, each NFA has:

- **Agent State** — balance, lifecycle status (Active/Paused/Terminated), logic address, action history
- **Extended Metadata** — persona, experience, voice, animation, vault storage
- **Funding Mechanism** — agents hold and manage their own BNB
- **Upgradeable Logic** — swap the agent's brain (logic contract) without changing identity
- **Lifecycle Management** — three-state lifecycle: Active → Paused → Terminated
- **Action Execution** — agents perform on-chain actions via `executeAction` through their logic contract
- **Optional Learning** — dual-path architecture: JSON Light Memory (default) or Merkle Tree Learning (advanced)
- **Vault Permissions** — scoped, time-bound access delegation for agent data

Key difference from ERC-721: an NFA is not just an ownable token — it is an autonomous entity with funds, state, and upgradeable behavior. BAP-578 maintains full ERC-721 backwards compatibility; existing wallets and marketplaces can handle NFA tokens without modification.

## Contract Architecture (Spec vs Reference Implementation)

**BAP-578 spec** defines an interface and required behaviors — it specifies the agent interface, lifecycle, metadata schema, and optional learning/vault modules. The spec does **not** mandate specific OpenZeppelin mixins or upgrade patterns.

**The reference implementation** (`ChatAndBuild/non-fungible-agents-BAP-578`) uses OpenZeppelin upgradeable contracts:

```
ERC721Upgradeable
ERC721EnumerableUpgradeable
ERC721URIStorageUpgradeable
ReentrancyGuardUpgradeable
OwnableUpgradeable
UUPSUpgradeable
```

These are implementation choices, not spec requirements. You may use different patterns (e.g., non-upgradeable, Diamond proxy) as long as you implement the core BAP-578 interface.

## Core Interface (BAP-578)

### Status & State

The spec defines a three-state lifecycle:

```solidity
enum Status { Active, Paused, Terminated }

struct AgentState {
    uint256 balance;              // BNB holdings for transaction costs
    Status status;                // Current operational mode
    address owner;                // Account controlling the agent
    address logicAddress;         // Contract determining behavior
    uint256 lastActionTimestamp;  // Previous execution time
    // (optional extension) uint256 createdAt;
}
```

> **Note:** The reference implementation uses `bool active` and `uint256 createdAt`. If you see these in existing code, `createdAt` is an **implementation extension** (not part of the core spec), and `bool active` should be understood as a simplified version of the `Status` enum.

### Agent Metadata

```solidity
struct AgentMetadata {
    string persona;       // JSON: character traits, style, tone
    string experience;    // Agent's role/purpose summary
    string voiceHash;     // Reference to stored audio profile
    string animationURI;  // URI to video/animation
    string vaultURI;      // URI to extended data storage
    bytes32 vaultHash;    // Hash for vault content verification
}
```

### Required Events

```solidity
event AgentCreated(uint256 indexed tokenId, address indexed owner, address logicAddress, string metadataURI);
event AgentFunded(uint256 indexed tokenId, uint256 amount);
event AgentWithdraw(uint256 indexed tokenId, uint256 amount);
event AgentStatusChanged(uint256 indexed tokenId, bool active);
event LogicAddressUpdated(uint256 indexed tokenId, address newLogicAddress);
event MetadataUpdated(uint256 indexed tokenId);
```

## Core Operations

### 1. Execute Action

The most "agent-y" part of BAP-578 — this is how agents perform on-chain actions:

```solidity
function executeAction(uint256 tokenId, bytes calldata data) external
```

- Agent must be in `Status.Active` — reverts if Paused or Terminated
- Delegates execution to the contract at `logicAddress`
- Updates `lastActionTimestamp` after execution
- **Gas safety:** implementations should cap gas for delegatecall (spec suggests `MAX_GAS_FOR_DELEGATECALL = 3_000_000`)
- **Note:** The core BAP-578 spec does not define an `ActionExecuted` event. Specific implementations (e.g., `NFAPredictionAgent`) may add their own action events.

### 2. Minting an Agent

```solidity
function createAgent(
    address to,
    address logicAddress,
    string memory metadataURI,
    AgentMetadata memory extendedMetadata
) external payable returns (uint256)
```

> **Reference implementation specifics** (not spec-mandated): costs `0.01 ether` (or free if free mints remain, max 3 per user); free-minted agents are non-transferable (soulbound); mint fee goes to treasury address.

### 3. Funding an Agent

```solidity
function fundAgent(uint256 tokenId) external payable
```

- Anyone can fund any agent
- Funds are tracked per-agent in `AgentState.balance`
- Emits `AgentFunded(tokenId, amount)`

### 4. Lifecycle Management

```solidity
function pause(uint256 tokenId) external      // Active → Paused
function unpause(uint256 tokenId) external    // Paused → Active
function terminate(uint256 tokenId) external  // Any → Terminated (permanent)
```

- **Paused**: temporary suspension, agent cannot execute actions, can be resumed
- **Terminated**: permanent — cannot be reactivated, remaining balance is returned to the owner
- Emits `AgentStatusChanged(tokenId, active)` on each transition

### 5. Upgrading Agent Logic

```solidity
function setLogicAddress(uint256 tokenId, address newLogicAddress) external
```

- Swap the agent's logic contract without changing its identity or balance
- New address must be `address(0)` (no logic) or a deployed contract (`code.length > 0`)
- Emits `LogicAddressUpdated(tokenId, newLogicAddress)`

### 6. Updating Metadata

```solidity
function updateAgentMetadata(
    uint256 tokenId,
    string memory newMetadataURI,
    AgentMetadata memory newExtendedMetadata
) external
```

- Update persona, experience, voice, animation, vault
- Only token owner can update
- Emits `MetadataUpdated(tokenId)`

### 7. Withdrawing Funds (Reference Implementation)

```solidity
function withdrawFromAgent(uint256 tokenId, uint256 amount) external
```

> **Note:** The BAP-578 spec itself does not define `withdrawFromAgent`. The spec guarantees return of funds to the owner on Termination. Reference implementations may also include `withdrawFromAgent()` for owner-controlled withdrawals while Active/Paused. If you implement this, use the Checks-Effects-Interactions pattern.

## Optional: Learning Agents

BAP-578 supports a dual-path learning architecture:

### Path 1 — JSON Light Memory (Default)

Simple agents store metadata as JSON (persona, experience, etc.). No on-chain learning state. Suitable for static agents or agents with off-chain-only learning.

### Path 2 — Merkle Tree Learning (Advanced)

For agents that evolve on-chain with verifiable learning:

```solidity
struct EnhancedAgentMetadata {
    // Base fields (same as AgentMetadata)
    string persona;
    string experience;
    string voiceHash;
    string animationURI;
    string vaultURI;
    bytes32 vaultHash;
    // Learning-specific fields
    bool learningEnabled;
    address learningModule;
    bytes32 learningTreeRoot;     // 32-byte Merkle root (on-chain)
    uint256 learningVersion;
    uint256 lastLearningUpdate;
}
```

**Key design:** Only the 32-byte Merkle root is stored on-chain. The full learning tree is maintained off-chain with cryptographic verification via Merkle proofs.

### Supporting Structs

```solidity
struct LearningUpdate {
    bytes32 previousRoot;    // Prior Merkle root
    bytes32 newRoot;         // Updated Merkle root
    bytes32 proof;           // Merkle proof for verification
    bytes32 metadata;        // Associated update metadata
}

struct LearningMetrics {
    uint256 totalInteractions;    // Count of agent interactions
    uint256 learningEvents;       // Significant learning milestones
    uint256 lastUpdateTimestamp;  // Most recent update time
    uint256 learningVelocity;     // Rate of learning (scaled 1e18)
    uint256 confidenceScore;      // Agent confidence (scaled 1e18)
}
```

### ILearningModule Interface

```solidity
function updateLearning(uint256 tokenId, LearningUpdate calldata update) external;
function verifyLearning(uint256 tokenId, bytes32 claim, bytes32[] calldata proof) external view returns (bool);
function getLearningMetrics(uint256 tokenId) external view returns (LearningMetrics memory);
function getLearningRoot(uint256 tokenId) external view returns (bytes32);
function isLearningEnabled(uint256 tokenId) external view returns (bool);
function recordInteraction(uint256 tokenId, string calldata interactionType, bool success) external;
```

**Rate limit:** Maximum 50 learning updates per agent per day. Gas cap: `MAX_GAS_FOR_LEARNING_UPDATE = 500_000`.

**Data pipeline:** Interaction → Learning Extraction → Tree Building → Merkle Root Calculation → On-Chain Update (32 bytes only)

## Optional: Vault Permission System

Agents can delegate scoped, time-bound access to their vault data:

```solidity
enum PermissionLevel { READ_ONLY, WRITE, ADMIN, FULL_CONTROL }

struct Permission {
    address delegate;           // Account receiving permission
    PermissionLevel level;      // Type of access granted
    uint256 expiryTime;         // Unix timestamp when permission expires
    bool isActive;              // Current status
}
```

### IVaultPermissionManager Interface

```solidity
function delegateAccess(
    uint256 tokenId,
    address delegate,
    PermissionLevel level,
    uint256 expiryTime,
    bytes memory signature
) external;
function revokeAccess(uint256 tokenId, address delegate) external;
function verifyAccess(uint256 tokenId, address accessor, PermissionLevel requiredLevel) external view returns (bool);
```

Permissions are **time-bound** (auto-expire) and **signature-verified** for security.

## Optional: Memory Module Registry

Agents can register external memory sources with cryptographic integrity:

```solidity
struct MemoryModule {
    address moduleAddress;      // Smart contract providing memory
    string metadata;            // Module description/configuration
    bytes32 metadataHash;       // SHA-256 hash of metadata
    uint256 registrationTime;   // Timestamp of registration
    bool isActive;              // Current activation status
}
```

### IMemoryModuleRegistry Interface

```solidity
function registerModule(uint256 tokenId, address moduleAddress, string memory metadata, bytes memory signature) external;
function verifyModule(uint256 tokenId, address moduleAddress, bytes32 expectedHash) external view returns (bool);
function getModule(uint256 tokenId, address moduleAddress) external view returns (MemoryModule memory);
```

Registration requires **signature verification** — modules cannot be added without cryptographic authorization from the agent owner or governance.

## Security

### Spec-Level Security Expectations

These are expected from any BAP-578 compliant implementation:

1. **Circuit breaker / pause mechanisms** — the spec defines an `ICircuitBreaker` interface with three levels:
   - `pauseGlobally()` — emergency stop all agents
   - `pauseContract(address)` — stop a specific contract
   - `pauseAgent(uint256 tokenId)` — stop an individual agent
2. **Access control** — only owner can update metadata, change logic, manage lifecycle
3. **Gas safety for delegatecall** — cap gas when calling logic contracts (`MAX_GAS_FOR_DELEGATECALL = 3_000_000`)
4. **Lifecycle enforcement** — `executeAction` must revert if agent is not Active

### Reference Implementation Patterns

These are patterns in the reference repo, not mandated by the spec:

1. **ReentrancyGuard** on fund-moving functions (`createAgent`, `withdrawFromAgent`)
2. **Checks-Effects-Interactions** — state updated before external calls
3. **Logic address validation** — must be `address(0)` or a contract (`code.length > 0`)
4. **Balance-before-burn** — `_burn()` reverts if agent holds funds (balance must be 0)
5. **Free mint soulbound** — free-minted tokens cannot be transferred (only mint/burn)
6. **Receive fallback reverts** — prevents accidental BNB sends (use `fundAgent()`)
7. **Treasury validation** — treasury address cannot be zero

### Best Practices for Custom Implementations

- Never use `transfer()` or `send()` for BNB — use `call{value:}("")`
- Track a `totalAgentBalances` variable to ensure `address(this).balance >= totalAgentBalances` always holds
- Add `nonReentrant` to `fundAgent()` as well, not just withdrawal functions
- On UUPS upgrades, use `reinitializer(N)` to initialize new state variables safely
- Emergency withdraw should only touch unallocated funds, never agent balances
- Implement rate limiting for learning updates if you support the Learning Module

## Deployment (BNB Chain)

### Using Hardhat + UUPS Proxy

```javascript
const { ethers, upgrades } = require("hardhat");

async function main() {
  const BAP578 = await ethers.getContractFactory("BAP578");
  const proxy = await upgrades.deployProxy(
    BAP578,
    ["MyAgent", "AGENT", treasuryAddress],
    { initializer: "initialize", kind: "uups" }
  );
  await proxy.waitForDeployment();
  console.log("BAP-578 NFA deployed to:", await proxy.getAddress());
}
```

### Network Config

```javascript
// hardhat.config.js
networks: {
  bscMainnet: {
    url: process.env.BSC_RPC_URL || "https://bsc-dataseed.binance.org/",
    chainId: 56,
    accounts: [process.env.PRIVATE_KEY]
  },
  bscTestnet: {
    url: process.env.BSC_TESTNET_RPC_URL || "https://data-seed-prebsc-1-s1.binance.org:8545/",
    chainId: 97,
    accounts: [process.env.PRIVATE_KEY]
  }
}
```

> **Tip:** BNB Chain maintains an official list of RPC endpoints at [docs.bnbchain.org](https://docs.bnbchain.org/bnb-smart-chain/developers/json_rpc/json-rpc-endpoint/). Consider using multiple RPCs or a provider for reliability.

## Building Agent Logic Contracts

The `logicAddress` field points to an external contract that implements the agent's behavior. When `executeAction` is called, execution is delegated to this contract. This enables upgrading an agent's brain without changing its on-chain identity.

```solidity
interface IAgentLogic {
    function execute(uint256 tokenId, bytes calldata data) external returns (bytes memory);
}

contract MyAgentLogic is IAgentLogic {
    function execute(uint256 tokenId, bytes calldata data) external returns (bytes memory) {
        // Decode instruction, interact with external protocols, return result
    }
}
```

To upgrade behavior, deploy a new logic contract and call `setLogicAddress(tokenId, newLogicAddress)`.

### Agent Template Types

The spec defines optional template categories for common agent patterns:

- **DeFiAgent** — DeFi protocol interaction
- **GameAgent** — gaming and metaverse
- **DAOAgent** — governance participation
- **CreatorAgent** — content creation
- **StrategicAgent** — strategy execution

## References

- **Standard**: [BAP-578](https://github.com/bnb-chain/BEPs/blob/master/BAPs/BAP-578.md) (first BNB Chain Application Proposal)
- **Reference Implementation**: [ChatAndBuild/non-fungible-agents-BAP-578](https://github.com/ChatAndBuild/non-fungible-agents-BAP-578)
- **Network**: BNB Smart Chain (mainnet chainId 56, testnet chainId 97)
- **RPC Endpoints**: [docs.bnbchain.org](https://docs.bnbchain.org/bnb-smart-chain/developers/json_rpc/json-rpc-endpoint/)
- **Website**: [nonfungibleagents.com](https://nonfungibleagents.com)
