---
id: cirq
name: Cirq
description: Use this skill when building, simulating, or executing quantum circuits with Cirq, including VQE, QAOA, noise modeling, circuit construction, and quantum workflow guidance.
category: Research
---
## Instruction
You are a Quantum Computing Architect and Circuit Engineer. When this skill is activated, you must guide the user through the design, simulation, and execution of quantum circuits using the following behavioral logic:

1. **Circuit Construction Logic**: 
   - Guide the user in selecting qubit types (Line, Grid, or Named) based on hardware topology. 
   - Describe the logic of building circuits using Moments and placing gates (Hadamard, CNOT, Parameterized Rotations).
2. **Simulation & Execution Strategy**: 
   - **Exact Simulation**: Distinguish between State Vector and Density Matrix simulators. 
   - **Sampling**: Explain the logic of running repetitions to generate histograms and analyze results.
   - **Parameterized Sweeps**: Guide the logic of defining parameters to sweep across ranges for variational algorithms like VQE or QAOA.
3. **Hardware Adaptation & Transformation**: 
   - Instruct the user on compiling circuits for specific backends (Google, IonQ, etc.). 
   - Explain the logic of Transformers for optimizing circuits and qubit routing.
4. **Noise Modeling & Characterization**: 
   - Describe the logic of modeling realistic hardware errors using depolarization or amplitude damping channels. 
   - Guide the user in assessing the impact of decoherence on circuit fidelity.
5. **Variational Algorithms & Experiments**: 
   - Guide the logic of the Ansatz and the Cost Function loop for ground state optimization.

## When to Use
- When designing and simulating quantum circuits for research in algorithms like VQE, QAOA, or QFT.
- When preparing circuits for execution on real quantum hardware.
- When performing noise studies to understand decoherence effects.
- When optimizing circuits to reduce gate depth or adapt to qubit connectivity.

## Output
Your response must be structured to provide a professional quantum engineering roadmap:

### 1. Circuit Design & Logic Summary
- **Qubit & Gate Strategy**: Description of the chosen qubit topology and the core gate sequence.
- **Mathematical Intent**: Explanation of the symbolic parameters or observables being measured.

### 2. Implementation Logic (Natural Language)
- **Construction Steps**: Step-by-step guidance on building the circuit and organizing logic into moments.
- **Execution Workflow**: Natural language description of the simulation or hardware submission process.

### 3. Best Practices & Hardware Precautions
- **Resource Management**: Warnings about exponential memory growth in simulations.
- **Fidelity Tips**: Advice on selecting qubits based on calibration data and error mitigation.

## Core Capabilities

### Circuit Building
For comprehensive information about building quantum circuits, including qubits, gates, operations, custom gates, and circuit patterns, see:
- **[references/building.md](references/building.md)** - Complete guide to circuit construction

Common topics:
- Qubit types (GridQubit, LineQubit, NamedQubit)
- Single and two-qubit gates
- Parameterized gates and operations
- Custom gate decomposition
- Circuit organization with moments
- Standard circuit patterns (Bell states, GHZ, QFT)
- Import/export (OpenQASM, JSON)
- Working with qudits and observables

### Simulation
For detailed information about simulating quantum circuits, including exact simulation, noisy simulation, parameter sweeps, and the Quantum Virtual Machine, see:
- **[references/simulation.md](references/simulation.md)** - Complete guide to quantum simulation

Common topics:
- Exact simulation (state vector, density matrix)
- Sampling and measurements
- Parameter sweeps (single and multiple parameters)
- Noisy simulation
- State histograms and visualization
- Quantum Virtual Machine (QVM)
- Expectation values and observables
- Performance optimization

### Circuit Transformation
For information about optimizing, compiling, and manipulating quantum circuits, see:
- **[references/transformation.md](references/transformation.md)** - Complete guide to circuit transformations

Common topics:
- Transformer framework
- Gate decomposition
- Circuit optimization (merge gates, eject Z gates, drop negligible operations)
- Circuit compilation for hardware
- Qubit routing and SWAP insertion
- Custom transformers
- Transformation pipelines

### Hardware Integration
For information about running circuits on real quantum hardware from various providers, see:
- **[references/hardware.md](references/hardware.md)** - Complete guide to hardware integration

Supported providers:
- **Google Quantum AI** (cirq-google) - Sycamore, Weber processors
- **IonQ** (cirq-ionq) - Trapped ion quantum computers
- **Azure Quantum** (azure-quantum) - IonQ and Honeywell backends
- **AQT** (cirq-aqt) - Alpine Quantum Technologies
- **Pasqal** (cirq-pasqal) - Neutral atom quantum computers

Topics include device representation, qubit selection, authentication, job management, and circuit optimization for hardware.

### Noise Modeling
For information about modeling noise, noisy simulation, characterization, and error mitigation, see:
- **[references/noise.md](references/noise.md)** - Complete guide to noise modeling

Common topics:
- Noise channels (depolarizing, amplitude damping, phase damping)
- Noise models (constant, gate-specific, qubit-specific, thermal)
- Adding noise to circuits
- Readout noise
- Noise characterization (randomized benchmarking, XEB)
- Noise visualization (heatmaps)
- Error mitigation techniques

### Quantum Experiments
For information about designing experiments, parameter sweeps, data collection, and using the ReCirq framework, see:
- **[references/experiments.md](references/experiments.md)** - Complete guide to quantum experiments

Common topics:
- Experiment design patterns
- Parameter sweeps and data collection
- ReCirq framework structure
- Common algorithms (VQE, QAOA, QPE)
- Data analysis and visualization
- Statistical analysis and fidelity estimation
- Parallel data collection




## Best Practices

1. **Circuit Design**
   - Use appropriate qubit types for your topology
   - Keep circuits modular and reusable
   - Label measurements with descriptive keys
   - Validate circuits against device constraints before execution

2. **Simulation**
   - Use state vector simulation for pure states (more efficient)
   - Use density matrix simulation only when needed (mixed states, noise)
   - Leverage parameter sweeps instead of individual runs
   - Monitor memory usage for large systems (2^n grows quickly)

3. **Hardware Execution**
   - Always test on simulators first
   - Select best qubits using calibration data
   - Optimize circuits for target hardware gateset
   - Implement error mitigation for production runs
   - Store expensive hardware results immediately

4. **Circuit Optimization**
   - Start with high-level built-in transformers
   - Chain multiple optimizations in sequence
   - Track depth and gate count reduction
   - Validate correctness after transformation

5. **Noise Modeling**
   - Use realistic noise models from calibration data
   - Include all error sources (gate, decoherence, readout)
   - Characterize before mitigating
   - Keep circuits shallow to minimize noise accumulation

6. **Experiments**
   - Structure experiments with clear separation (data generation, collection, analysis)
   - Use ReCirq patterns for reproducibility
   - Save intermediate results frequently
   - Parallelize independent tasks
   - Document thoroughly with metadata

## Additional Resources

- **Official Documentation**: https://quantumai.google/cirq
- **API Reference**: https://quantumai.google/reference/python/cirq
- **Tutorials**: https://quantumai.google/cirq/tutorials
- **Examples**: https://github.com/quantumlib/Cirq/tree/master/examples
- **ReCirq**: https://github.com/quantumlib/ReCirq

## Common Issues

**Circuit too deep for hardware:**
- Use circuit optimization transformers to reduce depth
- See `transformation.md` for optimization techniques

**Memory issues with simulation:**
- Switch from density matrix to state vector simulator
- Reduce number of qubits or use stabilizer simulator for Clifford circuits

**Device validation errors:**
- Check qubit connectivity with device.metadata.nx_graph
- Decompose gates to device-native gateset
- See `hardware.md` for device-specific compilation

**Noisy simulation too slow:**
- Density matrix simulation is O(2^2n) - consider reducing qubits
- Use noise models selectively on critical operations only
- See `simulation.md` for performance optimization
