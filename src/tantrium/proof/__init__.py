"""Exact dyadic proof primitives — rational arithmetic, no approximation."""
from tantrium.proof.certificate import Cell, Certificate, TransportEdge, Q
from tantrium.proof.dyadic_flow import solve_greedy, FlowPolicy

__all__ = ["Cell", "Certificate", "TransportEdge", "Q", "solve_greedy", "FlowPolicy"]
