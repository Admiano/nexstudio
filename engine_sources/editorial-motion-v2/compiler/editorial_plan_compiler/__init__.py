"""Editorial Plan Compiler: NexMind P8 treatment decision -> gate-checked EditorialPlan per native aspect.

    from editorial_plan_compiler import compile_film, write_outputs, FilmTreatment, TreatmentError

The compiler realises structured decisions; it never reads script wording to
route layout, motif, figure or sound. Anything outside the bounded vocabulary
raises ``TreatmentError`` with a coded replan reason for P8.
"""
from .compiler import COMPILER_VERSION, PLAN_SCHEMA, compile_film, write_outputs
from .contracts import SCHEMA as TREATMENT_SCHEMA
from .contracts import FilmTreatment, TreatmentError

__all__ = [
    'COMPILER_VERSION',
    'PLAN_SCHEMA',
    'TREATMENT_SCHEMA',
    'FilmTreatment',
    'TreatmentError',
    'compile_film',
    'write_outputs',
]
