# Small Feedback Arc Set (sfas)
Efficient implementation of a greedy algorithm for computing small feedback arc sets in directed weighted multi-graphs.
This implementation is an adaptation of the algorithm described in Section 2.3 of [this](http://www.vldb.org/pvldb/vol10/p133-simpson.pdf) article, with additional generalization to support weights and parallel edges.

## Description
Given a weighted directed graph, calculates linear arrangement of the nodes that minimizes (greedily) the number of backward edges (feedback arc set).
In particular, removing the set of edges going backward in the resulting order breaks all directed cycles in the graph.

## Interface
### Input:
1. connections: list of edges, each represented as a 3-item list consisting of [<from node>, <to node>, <edge weight>]
1. verbosity: prints progress and other stats for values >0
1. random_seed: randomness is in picking the next "greedy" step among equally qualified ones
### Output:
1. list with all nodes, ordered so that the total weight of edges going backwards (w.r.t. this order) is small

## Install
`pip install sfas`

## Example usage
```
from sfas import greedy

graph = [
    ['a', 'b', 1],
    ['b', 'c', 1],
    ['c', 'a', 2],
]
greedy.compute_order(graph, verbosity=0, random_seed=0)
```
#### output
```
['c', 'a', 'b']
```

## Questions / suggestions welcome
`arie.matsliah@gmail.com`