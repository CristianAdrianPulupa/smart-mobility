def optimize_route(distance_matrix):
    if not distance_matrix:
        raise ValueError("La matriz de distancias está vacía.")

    return list(range(len(distance_matrix)))