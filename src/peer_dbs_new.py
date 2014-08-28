# This code is distributed under the GNU General Public License (see
# THE_GENERAL_GNU_PUBLIC_LICENSE.txt for extending this information).
# Copyright (C) 2014, the P2PSP team.
# http://www.p2psp.org

# {{{

from __future__ import print_function
import threading
import sys
import socket
import struct
from color import Color
import common
import time
from _print_ import _print_
from peer_ims import Peer_IMS

# }}}

# Some useful definitions.
ADDR = 0
PORT = 1

# DBS: Data Broadcasting Set of rules
class Peer_DBS(Peer_IMS):
    # {{{

    # {{{ Class "constants"

    MAX_CHUNK_DEBT = 32

    # }}}

    def __init__(self, peer):
        # {{{

        sys.stdout.write(Color.yellow)
        _print_("Peer DBS")
        sys.stdout.write(Color.none)

        threading.Thread.__init__(self)

        self.splitter_socket = peer.splitter_socket
        self.player_socket = peer.player_socket
        self.buffer_size = peer.buffer_size
        self.chunk_format_string = peer.chunk_format_string
        self.splitter = peer.splitter
        self.chunk_size = peer.chunk_size

        _print_("max_chunk_debt =", self.MAX_CHUNK_DEBT)
        
        # }}}

    def say_goodbye(self, node):
        # {{{

        self.team_socket.sendto('', node)

        # }}}

    def receive_the_number_of_peers(self):
        # {{{

        self.debt = {}      # Chunks debts per peer.
        self.peer_list = [] # The list of peers structure.

        sys.stdout.write(Color.green)
        _print_("Requesting the list of peers to", self.splitter_socket.getpeername())
        self.number_of_peers = socket.ntohs(struct.unpack("H",self.splitter_socket.recv(struct.calcsize("H")))[0])
        _print_("The size of the team is", self.number_of_peers, "(apart from me)")

        sys.stdout.write(Color.none)

        # }}}
        
    def listen_to_the_team(self):
        # {{{ Create "team_socket" (UDP) as a copy of "splitter_socket" (TCP)

        self.team_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # In Windows systems this call doesn't work!
            self.team_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except Exception, e:
            print (e)
            pass
        self.team_socket.bind(('', self.splitter_socket.getsockname()[PORT]))

        # This is the maximum time the peer will wait for a chunk
        # (from the splitter or from another peer).
        self.team_socket.settimeout(1)

        # }}}

    def unpack_message(self, message):
        # {{{

        chunk_number, in_out, peer, chunk = struct.unpack(self.chunk_format_string, message)
        chunk_number = socket.ntohs(chunk_number)
        IP_addr, port = struct.unpack("4sH", incomming_peer)
        incomming_peer = (socket.inet_ntoa(incomming_peer), socket.ntohs(port))
        
        return chunk_number, in_out, peer, chunk

        # }}}
        
    def receive_a_chunk(self):
        try:
            message, sender = self.receive_the_next_message()

            chunk_number, in_out, peer, chunk = self.unpack_message(message)

            self.chunks[chunk_number % self.buffer_size] = chunk
            self.received[chunk_number % self.buffer_size] = True

            if sender == self.splitter:
                # {{{ Retransmit the previous splitter's message in burst transmission mode

                while( (self.receive_and_feed_counter < len(self.peer_list)) and (self.receive_and_feed_counter > 0) ):
                    peer = self.peer_list[self.receive_and_feed_counter]
                    self.team_socket.sendto(self.receive_and_feed_previous, peer)
                    self.sendto_counter += 1

                    self.debt[peer] += 1
                    if self.debt[peer] > self.MAX_CHUNK_DEBT:
                        del self.debt[peer]
                        self.peer_list.remove(peer)
                        print (Color.red, peer, 'removed by unsupportive', Color.none)

                    self.receive_and_feed_counter += 1

                self.receive_and_feed_counter = 0
                self.receive_and_feed_previous = message

                # }}}
            else:
                # {{{ Retransmit the previous splitter's message in congestion avoid transmission mode

                if ( self.receive_and_feed_counter < len(self.peer_list) and ( self.receive_and_feed_previous != '') ):
                    peer = self.peer_list[self.receive_and_feed_counter]
                    self.team_socket.sendto(self.receive_and_feed_previous, peer)
                    self.sendto_counter += 1

                    self.debt[peer] += 1
                    if self.debt[peer] > self.MAX_CHUNK_DEBT:
                        del self.debt[peer]
                        self.peer_list.remove(peer)
                        print (Color.red, peer, 'removed by unsupportive', Color.none)

                    self.receive_and_feed_counter += 1

                # }}}

            if in_out == 'I':
                if peer not in self.peer_list:
                    # {{{ Insert the incomming peer in the list of peers

                    self.peer_list.append(incomming_peer) # Ojo, colocar como siguiente, no al final
                    self.debt[incomming_peer] = 0
                    _print_(Color.green, incomming_peer, 'added by chunk', chunk_number, Color.none)

                    # }}}
            else:
                if peer in self.peer_list:
                    sys.stdout.write(Color.red)
                    print (self.team_socket.getsockname(), '\b: received "goodbye" from', peer)
                    sys.stdout.write(Color.none)
                    self.peer_list.remove(peer)
                    del self.debt[peer]

            self.debt[sender] -= 1

        except socket.timeout:
            return -1

    def receive_a_chunk(self):
        # {{{ Now, receive and send.

        try:
            # {{{ Receive and send

            message, sender = self.receive_the_next_message()

            if len(message) == struct.calcsize(self.chunk_format_string):
                # {{{ A video chunk has been received

                chunk_number = self.unpack_and_store_chunk(message)

                if sender == self.splitter:
                    # {{{ Send the previous chunk in burst sending

                    # mode if the chunk has not been sent to all
                    # the peers of the list of peers.

                    # {{{ debug

                    if __debug__:
                        _print_(self.team_socket.getsockname(), \
                            Color.red, "<-", Color.none, chunk_number, "-", sender)

                    # }}}

                    while( (self.receive_and_feed_counter < len(self.peer_list)) and (self.receive_and_feed_counter > 0) ):
                        peer = self.peer_list[self.receive_and_feed_counter]
                        self.team_socket.sendto(self.receive_and_feed_previous, peer)
                        self.sendto_counter += 1

                        # {{{ debug

                        if __debug__:
                            print (self.team_socket.getsockname(), "-",\
                                socket.ntohs(struct.unpack(self.chunk_format_string, \
                                                               self.receive_and_feed_previous)[0]),\
                                Color.green, "->", Color.none, peer)

                        # }}}

                        self.debt[peer] += 1
                        if self.debt[peer] > self.MAX_CHUNK_DEBT:
                            del self.debt[peer]
                            self.peer_list.remove(peer)
                            print (Color.red, peer, 'removed by unsupportive', Color.none)

                        self.receive_and_feed_counter += 1

                    self.receive_and_feed_counter = 0
                    self.receive_and_feed_previous = message

                   # }}}
                else:
                    # {{{ The sender is a peer

                    # {{{ debug

                    if __debug__:
                        print (self.team_socket.getsockname(), \
                            Color.green, "<-", Color.none, chunk_number, "-", sender)

                    # }}}

                    if sender not in self.peer_list:
                        # The peer is new
                        self.peer_list.append(sender)
                        self.debt[sender] = 0
                        print (Color.green, sender, 'added by chunk', \
                            chunk_number, Color.none)
                    else:
                        self.debt[sender] -= 1

                    # }}}

                # {{{ A new chunk has arrived from a peer and the
                # previous must be forwarded to next peer of the
                # list of peers.
                if ( self.receive_and_feed_counter < len(self.peer_list) and ( self.receive_and_feed_previous != '') ):
                    # {{{ Send the previous chunk in congestion avoiding mode.

                    peer = self.peer_list[self.receive_and_feed_counter]
                    self.team_socket.sendto(self.receive_and_feed_previous, peer)
                    self.sendto_counter += 1

                    self.debt[peer] += 1
                    if self.debt[peer] > self.MAX_CHUNK_DEBT:
                        del self.debt[peer]
                        self.peer_list.remove(peer)
                        print (Color.red, peer, 'removed by unsupportive', Color.none)

                    # {{{ debug

                    if __debug__:
                        print (self.team_socket.getsockname(), "-", \
                            socket.ntohs(struct.unpack(self.chunk_format_string, self.receive_and_feed_previous)[0]),\
                            Color.green, "->", Color.none, peer)

                    # }}}

                    self.receive_and_feed_counter += 1

                    # }}}
                # }}}
                
                return chunk_number

                # }}}
            else:
                # {{{ A control chunk has been received
                if sender in self.peer_list:
                    sys.stdout.write(Color.red)
                    print (self.team_socket.getsockname(), '\b: received "goodbye" from', sender)
                    sys.stdout.write(Color.none)
                    self.peer_list.remove(sender)
                    del self.debt[sender]
                return -1

                # }}}

            # }}}
        except socket.timeout:
            return -2

        # }}}

    def keep_the_buffer_full(self):
        # {{{

        Peer_IMS.keep_the_buffer_full(self)
        if (self.played_chunk % self.debt_memory) == 0:
            for i in self.debt:
                self.debt[i] /= 2

        if __debug__:
            sys.stdout.write(Color.cyan)
            print ("Number of peers in the team:", len(self.peer_list)+1)
            print (self.team_socket.getsockname(),)
            for p in self.peer_list:
                print (p,)
            print ()
            sys.stdout.write(Color.none)

        # }}}

    def polite_farewell(self):
        # {{{

        print('Goodbye!')
        for x in xrange(3):
            self.receive_a_chunk()
            self.say_goodbye(self.splitter)
        for peer in self.peer_list:
            self.say_goodbye(peer)

        # }}}

    def buffer_data(self):
        # {{{

        # Number of times that the previous received chunk has been sent
        # to the team. If this counter is smaller than the number
        # of peers in the team, the previous chunk must be sent in the
        # burst mode because a new chunk from the splitter has arrived
        # and the previous received chunk has not been sent to all the
        # peers of the team. This can happen when one o more chunks
        # that were routed towards this peer have been lost.
        self.receive_and_feed_counter = 0

        # This "private and static" variable holds the previous chunk
        # received from the splitter. It is used to send the previous
        # received chunk in the congestion avoiding mode. In that
        # mode, the peer sends a chunk only when it received a chunk
        # from another peer or om the splitter.
        self.receive_and_feed_previous = ""

        self.sendto_counter = 0

        self.debt_memory = 1 << self.MAX_CHUNK_DEBT

        Peer_IMS.buffer_data(self)

        # }}}
        
    def run(self):
        # {{{

        Peer_IMS.peers_life(self)
        self.polite_farewell()

        # }}}

    def am_i_a_monitor(self):
        if self.number_of_peers == 0:
            # Only the first peer of the team is the monitor peer
            return True
        else:
            return False
        #message = self.splitter_socket.recv(struct.calcsize("c"))
        #if struct.unpack("c", message)[0] == '1':
        #    return True
        #else:
        #    return False

    # }}}