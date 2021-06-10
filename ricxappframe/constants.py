from dataclasses import dataclass


@dataclass(frozen=True)
class SDLNamespaces:
    """
    This dataclass has namespace information about the well-known usecase.
    """
    E2_MANAGER = "e2Manager"  # Namespace where rnib information is stored


sdl_namespaces = SDLNamespaces()
