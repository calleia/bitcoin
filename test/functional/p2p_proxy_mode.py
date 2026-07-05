#!/usr/bin/env python3
# Copyright (c) 2026-present The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Test -proxymode.

A pruned node started with -proxymode that receives a getdata request for a
block it no longer has fetches the block from another peer and relays it back
to the requesting peer.
"""

from test_framework.messages import (
    CInv,
    MSG_BLOCK,
    MSG_WITNESS_FLAG,
    msg_getdata,
)
from test_framework.p2p import (
    P2PInterface,
    p2p_lock,
)
from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import (
    assert_equal,
    assert_raises_rpc_error,
)


class P2PProxyModeTest(BitcoinTestFramework):
    def set_test_params(self):
        self.num_nodes = 2
        self.extra_args = [
            [],
            ["-fastprune", "-prune=1", "-proxymode"],
        ]

    def run_test(self):
        full_node = self.nodes[0]
        proxy_node = self.nodes[1]

        self.log.info("Generate enough blocks for the proxy node to prune")
        self.generate(full_node, 600)

        self.log.info("Prune early blocks on the proxy node")
        proxy_node.pruneblockchain(300)
        pruned_block = full_node.getblockhash(2)
        assert_raises_rpc_error(-1, "Block not available (pruned data)", proxy_node.getblock, pruned_block)

        self.log.info("Request the pruned block from the proxy node via P2P")
        requester = proxy_node.add_p2p_connection(P2PInterface())
        requester.send_without_ping(msg_getdata([CInv(MSG_BLOCK | MSG_WITNESS_FLAG, int(pruned_block, 16))]))

        self.log.info("The proxy node fetches the block from the full node and relays it back")
        requester.wait_for_block(int(pruned_block, 16), timeout=30)

        self.log.info("The fetched block is stored on the proxy node again")
        self.wait_until(lambda: proxy_node.getblock(pruned_block)["hash"] == pruned_block, timeout=30)

        self.log.info("A repeated request is served directly from disk")
        with p2p_lock:
            requester.last_message.pop("block", None)
        requester.send_without_ping(msg_getdata([CInv(MSG_BLOCK | MSG_WITNESS_FLAG, int(pruned_block, 16))]))
        requester.wait_for_block(int(pruned_block, 16), timeout=30)

        self.log.info("Another pruned block can be proxied as well")
        pruned_block_2 = full_node.getblockhash(3)
        assert_raises_rpc_error(-1, "Block not available (pruned data)", proxy_node.getblock, pruned_block_2)
        requester.send_without_ping(msg_getdata([CInv(MSG_BLOCK | MSG_WITNESS_FLAG, int(pruned_block_2, 16))]))
        requester.wait_for_block(int(pruned_block_2, 16), timeout=30)


if __name__ == '__main__':
    P2PProxyModeTest(__file__).main()
