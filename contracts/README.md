# Aegis-rToken Contracts & Verification Boundary

This directory serves as the dedicated integration boundary for decentralized verification, consensus, and attestation infrastructure (e.g., on-chain state machines or cryptographic attestation registries).

## Purpose & Scope

The core Aegis trading system is fully autonomous and functions independently without requiring an active blockchain connection. However, high-integrity autonomous systems benefit from decentralized attestation. 

Future contracts developed in this directory may be utilized for:

1. **Event Verification**: Cryptographically proving the authenticity, source provenance, and arrival timestamp of market-moving news or data triggers.
2. **Consensus & Validation**: Multi-validator agreement or optimistic challenges over anomalous event interpretations.
3. **Strategy Decision Attestations**: On-chain hashing and anchoring of every decision tuple (`eventId`, `sentiment`, `confidence`, `marketSpread`, `riskVerdict`, `orderHash`) to guarantee tamper-proof audit trails.
4. **Auditability & Accountability**: Publicly verifiable record of paper-trading and live execution telemetry, ensuring no retroactive deletion or modification of trading records.

## Directory Structure

- `src/`: Smart contract source code (Intelligent contracts, Solidity, Vyper, etc.).
- Testing and deployment scripts for contracts will be maintained alongside their specific tooling frameworks.

## Current Status

- **Phase**: Architecture & integration boundary scaffolding.
- **Independence**: The core Aegis agent engine (`src/aegis_rtoken`) remains completely decoupled from and operational without this contract layer.
