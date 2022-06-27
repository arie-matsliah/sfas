# Small Feedback Arc Set (sfas)
Efficient implementation of a greedy algorithm for computing small feedback arc sets in directed weighted multi-graphs.
This implementation is an adaptation of the algorithm described in Section 2.3 of [this](http://www.vldb.org/pvldb/vol10/p133-simpson.pdf) article, with additional generalization to support weights and parallel edges.
## Description
Given a weighted directed graph, computes a topological sorting (linear order of the nodes) that minimizes (greedily) the number of backward edges - feedback arc set.
In particular, removing the set of edges going backward in the resulting order breaks all directed cycles in the graph.
## Install
`pip install sfas`
## Example usage
```
graph = [
    ['a', 'b', 1],
    ['a', 'c', 1],
    ['c', 'd', 2],
    ['d', 'a', 2],
]
```
![Input Graph](https://github.com/ariematsliah-princeton/sfas/raw/main/static/ex_graph_orig.png)
```
from sfas import greedy
ouput = greedy.compute_order(graph)
```
#### output
```
['c', 'd', 'a', 'b']
```
![Order with minimal FAS](https://github.com/ariematsliah-princeton/sfas/raw/main/static/ex_graph_sfas.png)
## Interface
### Params:
1. `connections : List[List[Any, Any, Int]]` - list of edges, each represented as a 3-item list consisting of `[<from node>, <to node>, <edge weight>]`
1. `verbosity : Int` - prints progress and other stats for values > 0
1. `random_seed : Int` randomness is in picking the next "greedy" step among equally qualified ones
### Result:
1. `List` with all nodes, ordered so that the total weight of edges going backwards (w.r.t. this order) is small
## Questions / suggestions welcome
`arie.matsliah@gmail.com`