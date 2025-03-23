import asyncio
from typing import Any, Callable, List, TypeVar, Dict, Awaitable

T = TypeVar("T")
InputType = TypeVar("InputType")
ResultType = TypeVar("ResultType")


async def run_tasks_in_parallel(
    process_function: Callable[[InputType], Awaitable[ResultType]],
    inputs: List[InputType],
    show_progress: bool = True,
    result_handler: Callable[[InputType, ResultType], None] = None,
) -> List[ResultType]:
    """
    Ejecuta múltiples tareas en paralelo usando asyncio.

    Args:
        process_function: La función asíncrona que se ejecutará para cada entrada
        inputs: Lista de elementos de entrada a procesar
        show_progress: Indica si se muestran mensajes de progreso
        result_handler: Callback opcional para manejar cada resultado cuando se completa

    Returns:
        Lista de resultados de todas las entradas procesadas
    """
    if show_progress:
        print(f"Procesando {len(inputs)} elementos en paralelo...\n")

    # Crear tareas para cada entrada
    tasks = [process_function(input_item) for input_item in inputs]

    # Procesar todas las tareas en paralelo
    results = await asyncio.gather(*tasks)

    # Manejar resultados si se proporciona un manejador
    if result_handler:
        for input_item, result in zip(inputs, results):
            result_handler(input_item, result)

    return results


async def run_dict_tasks_in_parallel(
    process_function: Callable[[Dict[str, Any]], Awaitable[ResultType]],
    input_dicts: List[Dict[str, Any]],
    show_progress: bool = True,
    result_handler: Callable[[Dict[str, Any], ResultType], None] = None,
) -> List[ResultType]:
    """
    Ejecuta múltiples tareas con entradas de diccionario en paralelo usando asyncio.

    Args:
        process_function: La función asíncrona que se ejecutará para cada diccionario de entrada
        input_dicts: Lista de diccionarios de entrada a procesar
        show_progress: Indica si se muestran mensajes de progreso
        result_handler: Callback opcional para manejar cada resultado cuando se completa

    Returns:
        Lista de resultados de todas las entradas procesadas
    """
    return await run_tasks_in_parallel(
        process_function=process_function,
        inputs=input_dicts,
        show_progress=show_progress,
        result_handler=result_handler,
    )
