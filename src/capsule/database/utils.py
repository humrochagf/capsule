from collections.abc import Iterable
from real_ladybug import QueryResult

def query_to_iterdict(query: QueryResult | list[QueryResult]) -> Iterable[dict]:
    for q in query:
        q.
