import random

def nodes_from_connections_table(connections_table):
    return set([r[0] for r in connections_table]).union(set([r[1] for r in connections_table]))

def adjacency_lists(connections_table, verbosity=0):
    node_list = nodes_from_connections_table(connections_table)
    input_lists = {n: [] for n in node_list}
    output_lists = {n: [] for n in node_list}
    for r in connections_table:
        input_lists[r[1]].append(r)
        output_lists[r[0]].append(r)
    if verbosity:
        print(f"Nodes: {len(node_list)}, "
              f"max out: {max([len(s) for s in output_lists.values()])}, "
              f"max in: {max([len(s) for s in input_lists.values()])}")
    return input_lists, output_lists


def percentage_str(part, whole):
    return f"{int(100 * float(part) / float(whole))}%"

# Calculates linear arrangement of the nodes that minimizes (greedily) the number of backward edges
# Implements Algorithm 1 from http://www.vldb.org/pvldb/vol10/p133-simpson.pdf
# Input:
#  - connections: list of edges, each represented as a 3-item list consisting of [<from node>, <to node>, <edge weight>]
#  - verbosity: prints progress and other stats for values >0
#  - random_seed: randomness is in picking the next "greedy" step among equally qualified ones
# Output:
#  - list with all nodes, ordered so that the total weight of edges going backwards (w.r.t. this order) is small
def compute_order(connections, verbosity=0, random_seed=0):
    total_edge_weight = sum([r[2] for r in connections])
    if verbosity > 0:
        print(f"Connections: {len(connections)}, total edge weight: {total_edge_weight}")

    # capture adjacency lists for all nodes (from the connections table)
    input_rows, output_rows = adjacency_lists(connections)

    # randomize
    random.seed(random_seed)
    connections = list(connections)
    random.shuffle(connections)
    node_ids = list(input_rows.keys())
    random.shuffle(node_ids)

    # optimization: map node ids to serial ids 0,...,N-1
    nodes_compacted = {k: i for i, k in enumerate(node_ids)}

    # builds a connection dictionary for a single node as follows:
    #  1. maps node ids to compact ids
    #  2. combines parallel edges (summing their weights)
    #  3. return a dictionary, where keys are compacted node ids of neighbors (either outgoing or incoming,
    #     depending on nidx), and values are the weights of edges connecting to them.
    def compact_dict(rows, nidx):
        cd = {}
        for r in rows:
            cn = nodes_compacted[r[nidx]]
            cd[cn] = cd.get(cn, 0) + r[2]
        return cd

    if verbosity > 2:
        print(f"Input adjacency: {input_rows}")
        print(f"Output adjacency: {output_rows}")

    # builds input/output connection dictionaries for all nodes (compacted)
    input_dict = {nodes_compacted[k]: compact_dict(v, 0) for k, v in input_rows.items()}
    output_dict = {nodes_compacted[k]: compact_dict(v, 1) for k, v in output_rows.items()}

    # sanity checks
    for nd, indict in input_dict.items():
        for ind, w in indict.items():
            assert output_dict[ind][nd] == w
    for nd, indict in output_dict.items():
        for ind, w in indict.items():
            assert input_dict[ind][nd] == w

    # this keeps track of the total sum of weights of all edges pointing backwards
    feedback_val = 0

    # Remove anti-parallel edges: we still might have anti-parallel edges of the form $e_1 = u \to v$ and
    # $e_2 = v \to u$ with $w_1$ and $w_2$ their respective weights. Without loss of generality, lets assume
    # $w_1 \leq w_2$; we remove $e_1$ from the graph, and update $w_2 = w_2 - w_1$. And we keep record of
    # the sum of all weights of the removed edges in 'feedback_val'.
    anti_parallel_edges = []
    for nd, indict in input_dict.items():
        for ind, w in indict.items():
            if nd < ind: # add each pair only once
                if nd in input_dict[ind]:
                    anti_parallel_edges.append((ind, nd))
    if anti_parallel_edges:
        print(f"Found {len(anti_parallel_edges)} anti-parallel edges")
        for (n1, n2) in anti_parallel_edges:
            w12 = output_dict[n1][n2]
            assert w12 == input_dict[n2][n1]
            w21 = output_dict[n2][n1]
            assert w21 == input_dict[n1][n2]
            if w12 > w21:
                del output_dict[n2][n1]
                del input_dict[n1][n2]
                output_dict[n1][n2] -= w21
                input_dict[n2][n1] -= w21
                feedback_val += w21
            else:
                del output_dict[n1][n2]
                del input_dict[n2][n1]
                output_dict[n2][n1] -= w12
                input_dict[n1][n2] -= w12
                feedback_val += w12
        print(f"Starting with feedback_val {feedback_val}")

    # sanity checks after removing anti-parallel edges
    for nd, indict in input_dict.items():
        for ind, w in indict.items():
            assert output_dict[ind][nd] == w
            assert nd not in input_dict[ind]
    for nd, indict in output_dict.items():
        for ind, w in indict.items():
            assert input_dict[ind][nd] == w
            assert nd not in output_dict[ind]

    # bucket keys are either 'sinks', 'sources' or the weight of outputs - weight of inputs (as in the algo described
    # in the paper, just weighted).
    def compute_bucket_key_for_node(n):
        if not output_dict.get(n):
            return 'sinks'
        elif not input_dict.get(n):
            return 'sources'
        else:
            return sum(output_dict[n].values()) - sum(input_dict[n].values())

    buckets = {}

    def insert_to_bucket(node, key):
        if key in buckets:
            buckets[key].add(node)
        else:
            buckets[key] = {node}

    def remove_from_bucket(node, key):
        buckets[key].remove(node)
        if not buckets[key]:
            del buckets[key]

    def pop_from_bucket(key):
        itm = buckets[key].pop()
        if not buckets[key]:
            del buckets[key]
        return itm

    # insert all nodes to buckets
    for n in range(len(nodes_compacted)):
        insert_to_bucket(node=n, key=compute_bucket_key_for_node(n))

    # keep index of node to bucket key for quick lookups
    node_to_bucket_key = {}
    for k, v in buckets.items():
        for n in v:
            node_to_bucket_key[n] = k

    if verbosity > 1:
        blengths = {k: len(v) for k, v in buckets.items()}
        print(f"Buckets: {blengths}")

    # see the algo description in sec 2.3 - left contains sources and "lots of outputs" nodes, right contains sinks
    left_list = []
    right_list = []

    # for periodic progress report
    next_report = 1
    num_nodes = len(nodes_compacted)

    # this will update all data structures upon removal of a node and it's assignment to one of left/right lists
    def update_removed_node(node):
        # update graph
        in_nodes = input_dict[node]
        for inode in in_nodes.keys():
            del output_dict[inode][node]

        out_nodes = output_dict[node]
        for onode in out_nodes.keys():
            del input_dict[onode][node]

        del input_dict[node]
        del output_dict[node]

        # update buckets and bucket key index
        for ionode in set(in_nodes.keys()).union(out_nodes.keys()):
            remove_from_bucket(node=ionode, key=node_to_bucket_key[ionode])
            new_key = compute_bucket_key_for_node(ionode)
            node_to_bucket_key[ionode] = new_key
            insert_to_bucket(node=ionode, key=new_key)

    # main algo execution loop. repeats untill all nodes have been assigned to left or right list
    while len(left_list) + len(right_list) < num_nodes:
        # check in for progress report
        if verbosity > 1 and len(left_list) + len(right_list) > next_report:
            pld = len(left_list) + len(right_list)
            print(f"Placed {pld} nodes ({percentage_str(pld, num_nodes)}) fs = {feedback_val} ({percentage_str(feedback_val, total_edge_weight)})")
            next_report += 1000

        # if there are sinks in remaining subgraph, assign them to the right list
        if buckets.get('sinks'):
            n = pop_from_bucket('sinks')
            right_list.append(n)
            if verbosity > 1:
                print(f"Removing {n} coz sink")
            update_removed_node(n)
        # if there are sources in remaining subgraph, assign them to the left list
        elif buckets.get('sources'):
            n = pop_from_bucket('sources')
            left_list.append(n)
            if verbosity > 1:
                print(f"Removing {n} coz source")
            update_removed_node(n)
        # if no sinks/sources in remaining subgraph, assign the node with largest out/in weight ration to the left list
        else:
            max_delta = max(buckets.keys() - {'sinks', 'sources'})
            n = pop_from_bucket(max_delta)
            left_list.append(n)
            max_delta_feedback = sum(input_dict[n].values())
            feedback_val += max_delta_feedback
            if verbosity > 1:
                print(f"Removing {n} coz delta {max_delta} (fs inc {max_delta_feedback})")
            update_removed_node(n)

    # right list needs to be reversed since sinks were appended to the end instead of beginning (impl detail)
    right_list.reverse()

    # go back from compacted ids to original node ids
    nodes_compacted_inverse = {k: v for v, k in nodes_compacted.items()}
    res = [nodes_compacted_inverse[n] for n in left_list + right_list]
    res_index = {v: k for k, v in enumerate(res)}

    # sanity check: the total weight of edges going backward in the computed order should equal the tracked weight
    fs = [r for r in connections if res_index[r[0]] > res_index[r[1]]]
    fsw = sum([r[2] for r in fs])
    assert fsw == feedback_val

    if verbosity > 0:
        print(f"Feedback size: {fsw}:{feedback_val} ({percentage_str(fsw, total_edge_weight)})")
        if verbosity > 1:
            print(f"Result: {res}")
            print(f"Feedback: {fs}")

    return res
