//
//  splitter_lrs.cc
//  P2PSP
//
//  This code is distributed under the GNU General Public License (see
//  THE_GNU_GENERAL_PUBLIC_LICENSE.txt for extending this information).
//  Copyright (C) 2016, the P2PSP team.
//  http://www.p2psp.org
//
//  LRS: Lost chunk Recovery Set of rules
//

#include "splitter_lrs.h"
#include "../util/trace.h"

namespace p2psp {
  using namespace std;
  using namespace boost;

  Splitter_LRS::Splitter_LRS() : Splitter_ACS(), buffer_(buffer_size_) {
    //magic_flags_ = Common::kLRS;
    TRACE("Initialized LRS");
  }

  Splitter_LRS::~Splitter_LRS() {}

  void Splitter_LRS::ProcessLostChunk(int lost_chunk_number, const boost::asio::ip::udp::endpoint &sender) {
    Splitter_DBS::ProcessLostChunk(lost_chunk_number, sender);
    std::vector<char> message = buffer_.at(lost_chunk_number % buffer_size_);
    asio::ip::udp::endpoint peer = peer_list_.at(0);
    
    system::error_code ec;
    
    // Send always to monitor peer
    team_socket_.send_to(asio::buffer(message), peer, 0, ec);
    
    if (ec) {
      ERROR("LRS - Error sending chunk: " << ec.message());
    }
    
    TRACE("Re-sending " << to_string(lost_chunk_number) << " to " << peer);
  }
  
  void Splitter_LRS::SendChunk(const std::vector<char> &message,
			       const boost::asio::ip::udp::endpoint &destination) {
    Splitter_DBS::SendChunk(message, destination);
    buffer_[chunk_number_ % buffer_size_] = message;
  }
}
