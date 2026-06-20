"""Exact dyadic proof primitives — rational arithmetic, no approximation."""

from tantrium.proof.certificate import Cell, Certificate, Q, TransportEdge
from tantrium.proof.dyadic_flow import FlowPolicy, solve_greedy

__all__ = ["Cell", "Certificate", "TransportEdge", "Q", "solve_greedy", "FlowPolicy"]
