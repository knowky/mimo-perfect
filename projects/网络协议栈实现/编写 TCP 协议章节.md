# 编写 TCP 协议章节

**任务**: 网络协议栈实现
**时间**: 2026-06-04T23:15:50.601079

# TCP 协议实现

## 1. 概述

TCP（Transmission Control Protocol，传输控制协议）是互联网协议栈中最核心的传输层协议之一，它位于 IP 层之上，为应用层提供**可靠、面向连接、基于字节流**的通信服务。TCP 的设计目标是在不可靠的网络层（IP）之上构建一个可靠的传输机制，确保数据能够无差错、不丢失、不重复且按序到达对端。

在本章中，我们将详细探讨 TCP 协议的核心机制与实现细节，包括：

*   **连接管理**：三次握手建立连接，四次挥手释放连接。
*   **可靠传输**：基于序列号、确认号和超时重传的可靠数据交付。
*   **流量控制**：使用滑动窗口机制防止发送方压垮接收方。
*   **拥塞控制**：采用慢启动、拥塞避免、快速重传和快速恢复等算法应对网络拥塞。

我们将从一个实现者的角度，结合关键数据结构和算法伪代码，深入解析这些机制。

## 2. TCP 报文段（Segment）格式

TCP 数据传输的基本单元是**报文段**。其首部结构至关重要，它包含了实现 TCP 各项功能所需的控制信息。

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Source Port          |       Destination Port        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        Sequence Number                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Acknowledgment Number                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Data |       |C|E|U|A|P|R|S|F|                               |
| Offset| Rsrvd |W|C|R|C|S|S|Y|I|            Window             |
|       |       |R|E|G|K|H|T|N|N|                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|           Checksum            |         Urgent Pointer        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Options (Variable)                         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                             Data                              |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

**关键字段说明**：

*   **源端口/目的端口 (Source/Destination Port)**：各占16位，标识发送和接收应用进程。
*   **序列号 (Sequence Number)**：32位。本报文段所发送数据的第一个字节的编号。在连接建立时，双方会交换一个初始序列号（ISN）。
*   **确认号 (Acknowledgment Number)**：32位。期望收到对方下一个报文段的第一个数据字节的编号。只有当 ACK 标志位被置位时，此字段才有效。
*   **数据偏移 (Data Offset)**：4位。指出 TCP 报文段的数据起始处距离 TCP 报文段起始处有多远，即首部长度。单位是32位字（即4字节）。
*   **标志位 (Flags)**：6位，用于控制连接和传输。
    *   **SYN**：同步序列号，用于连接建立。
    *   **ACK**：确认号字段有效。
    *   **FIN**：发送方完成发送任务，用于连接释放。
    *   **RST**：重置连接。
    *   **PSH**：提示接收方应立即将数据交付给应用层。
    *   **URG**：紧急指针字段有效。
*   **窗口 (Window)**：16位。用于流量控制，指示从本报文段的确认号开始，接收方当前允许发送方发送的数据量（以字节为单位）。
*   **校验和 (Checksum)**：16位。覆盖 TCP 首部和数据，用于检测传输中的错误。
*   **紧急指针 (Urgent Pointer)**：16位。指出本报文段中的紧急数据的末尾位置。只有当 URG 标志位置位时才有效。

## 3. 连接管理

### 3.1 连接建立：三次握手（Three-Way Handshake）

TCP 连接的建立是一个不对称的过程，旨在协商初始序列号（ISN）和确认双方的接收能力。

**过程描述**：

1.  **SYN**：客户端选择一个初始序列号 `client_isn`，并向服务器发送一个 SYN 报文段（`SYN=1, Seq=client_isn`）。此时客户端进入 `SYN_SENT` 状态。
2.  **SYN-ACK**：服务器收到 SYN 后，分配资源，选择自己的初始序列号 `server_isn`，并发送一个 SYN-ACK 报文段（`SYN=1, ACK=1, Seq=server_isn, Ack=client_isn+1`）。服务器进入 `SYN_RCVD` 状态。
3.  **ACK**：客户端收到 SYN-ACK 后，发送一个 ACK 报文段（`ACK=1, Seq=client_isn+1, Ack=server_isn+1`）。此报文段可以携带数据。客户端进入 `ESTABLISHED` 状态。服务器收到此 ACK 后，也进入 `ESTABLISHED` 状态。

**为什么需要三次？**
主要目的是防止**历史重复连接的初始化**。如果只进行两次握手，那么一个在网络中滞留的旧 SYN 报文段到达服务器后，服务器会误以为是一个新的连接请求并分配资源，从而造成资源浪费。三次握手中的第三步 ACK 可以让服务器确认这是一个有效的、当前的连接请求。

### 3.2 连接释放：四次挥手（Four-Way Handshake）

TCP 连接是**全双工**的，因此每个方向必须单独进行关闭。

**过程描述**（以客户端主动关闭为例）：

1.  **FIN**：客户端发送一个 FIN 报文段（`FIN=1, Seq=u`），表示它没有数据要发送了。客户端进入 `FIN_WAIT_1` 状态。
2.  **ACK**：服务器收到 FIN 后，发送一个 ACK 报文段（`ACK=1, Ack=u+1`），并进入 `CLOSE_WAIT` 状态。此时，从服务器到客户端的连接仍未关闭，服务器可能还有数据要发送。
3.  **FIN**：当服务器也没有数据要发送时，它发送自己的 FIN 报文段（`FIN=1, Seq=w`），进入 `LAST_ACK` 状态。
4.  **ACK**：客户端收到服务器的 FIN 后，发送一个 ACK 报文段（`ACK=1, Ack=w+1`），并进入 `TIME_WAIT` 状态。在等待 **2MSL（最大报文段生存时间）** 后，客户端关闭连接。服务器收到这个 ACK 后，立即关闭连接。

**`TIME_WAIT` 状态的意义**：
*   **保证可靠的连接终止**：确保最后一个 ACK 能够到达服务器。如果该 ACK 丢失，服务器会重传 FIN，`TIME_WAIT` 状态的客户端可以重发 ACK。
*   **让旧连接的报文段在网络中过期**：防止“已失效的连接请求报文段”出现在本连接中，影响到可能建立的新连接。

## 4. 可靠数据传输机制

### 4.1 序列号与确认

TCP 对每一个发送的字节都进行编号（序列号）。接收方通过累积确认的方式告知发送方：它已正确收到序列号 `Ack` 之前的所有数据，并期望接收序列号为 `Ack` 的数据。

### 4.2 超时重传

发送方为每个已发送但未确认的报文段设置一个**重传计时器（RTO）**。如果在计时器超时前未收到对应的 ACK，则认为该报文段丢失，并重传它。

**RTO 的计算**是关键，需要基于对网络往返时间（RTT）的测量进行动态调整（通常使用 Jacobson/Karels 算法）。基本思想是：
```
EstimatedRTT = (1-α)*EstimatedRTT + α*SampleRTT
DevRTT = (1-β)*DevRTT + β*|SampleRTT - EstimatedRTT|
RTO = EstimatedRTT + 4*DevRTT
```
其中 `α` 通常取 1/8，`β` 取 1/4。

### 4.3 快速重传

如果发送方连续收到 **3 个重复的 ACK**，则认为紧接着该确认号之后的报文段可能已经丢失。此时，发送方不等待 RTO 超时，而是立即重传该报文段，这称为**快速重传**。

## 5. 流量控制

**目的**：防止发送方发送过快，导致接收方缓冲区溢出。

**机制**：接收方在每个 ACK 报文段的 **窗口字段** 中，告知发送方自己接收缓冲区的剩余大小（即接收窗口 `rwnd`）。发送方维护一个**发送窗口**，其大小不能超过接收方通告的 `rwnd`。

**发送方操作**：
```
LastByteSent - LastByteAcked <= rwnd
```
其中 `LastByteSent` 是最后发送的字节编号，`LastByteAcked` 是最后被确认的字节编号。这个不等式确保已发送但未确认的数据量不超过接收窗口。

## 6. 拥塞控制

**目的**：防止过多的数据注入网络，避免网络中的路由器或链路过载。

**机制**：TCP 拥塞控制的核心是维护一个**拥塞窗口（cwnd）**。发送方实际的发送窗口 `swnd` 取值为：
```
swnd = min(cwnd, rwnd)
```

经典 TCP 拥塞控制包含四个阶段（以 Reno 版本为例）：

1.  **慢启动（Slow Start）**：
    *   连接开始时，`cwnd` 初始化为 1 个 MSS（最大报文段长度）。
    *   每收到一个 ACK，`cwnd` 就增加一个 MSS（即每个 RTT，`cwnd` 翻倍）。
    *   直到 `cwnd` 达到或超过慢启动阈值（`ssthresh`），进入拥塞避免阶段。

2.  **拥塞避免（Congestion Avoidance）**：
    *   每个 RTT，`cwnd` 增加 1 个 MSS（线性增长）。
    *   直到检测到网络拥塞（超时或收到3个重复ACK）。

3.  **快速重传与快速恢复（Fast Retransmit and Fast Recovery）**：
    *   当收到3个重复ACK时，发送方执行**快速重传**。
    *   随后进入**快速恢复**阶段：
        *   将 `ssthresh` 设置为当前 `cwnd` 的一半。
        *   将 `cwnd` 设置为新的 `ssthresh` + 3 个 MSS（因为收到了3个重复ACK）。
        *   每收到一个重复ACK，`cwnd` 增加 1 个 MSS。
        *   直到收到一个新的 ACK，将 `cwnd` 设置为 `ssthresh`，并进入拥塞避免阶段。

4.  **超时（Timeout）**：
    *   如果 RTO 超时，意味着网络发生了严重拥塞。
    *   将 `ssthresh` 设置为当前 `cwnd` 的一半。
    *   将 `cwnd` 重置为 1 个 MSS。
    *   重新开始慢启动。

## 7. 实现要点与伪代码

### 7.1 核心数据结构

```c
struct tcp_sock {
    // 连接四元组
    uint32_t local_ip, remote_ip;
    uint16_t local_port, remote_port;
    
    // 连接状态
    enum tcp_state state;
    
    // 序列号相关
    uint32_t snd_una; // 发送但未确认的第一个字节序列号
    uint32_t snd_nxt; // 下一个要发送的字节序列号
    uint32_t rcv_nxt; // 期望接收的下一个字节序列号
    
    // 窗口相关
    uint32_t snd_wnd; // 发送窗口大小
    uint32_t rcv_wnd; // 接收窗口大小
    uint32_t cwnd;    // 拥塞窗口大小
    uint32_t ssthresh;// 慢启动阈值
    
    // 计时器
    struct timer retransmit_timer;
    // ... 其他定时器
    
    // 缓冲区
    struct sk_buff_head send_queue; // 发送缓冲区
    struct sk_buff_head recv_queue; // 接收缓冲区
    
    // ... 其他状态变量
};
```

### 7.2 处理接收到的 ACK（简化伪代码）

```c
void tcp_ack(struct tcp_sock *sk, struct tcp_segment *seg) {
    uint32_t ack_num = seg->ack_num;
    
    // 1. 确认新数据
    if (after(ack_num, sk->snd_una)) {
        // 更新 snd_una
        sk->snd_una = ack_num;
        // 从发送队列移除已确认的数据
        remove_acknowledged_data(sk->send_queue, ack_num);
        // 重置重传计时器（如果没有未确认的数据，则关闭计时器）
        
        // 2. 更新拥塞窗口 (Congestion Avoidance)
        if (sk->state == CA_OPEN) {
            if (sk->cwnd < sk->ssthresh) {
                // 慢启动: 每个 ACK 增加 cwnd
                sk->cwnd += SMSS; // SMSS: 发送方 MSS
            } else {
                // 拥塞避免: 每个 RTT 增加约 1 个 MSS
                sk->cwnd += SMSS * SMSS / sk->cwnd;
            }
        }
    }
    
    // 3. 处理重复 ACK (快速重传/快速恢复)
    if (ack_num == sk->snd_una && !seg->len) { // 重复 ACK
        sk->dup_acks++;
        if (sk->dup_acks == 3) {
            // 快速重传
            tcp_fast_retransmit(sk);
            // 进入快速恢复状态
            sk->ssthresh = max(sk->cwnd/2, 2*SMSS);
            sk->cwnd = sk->ssthresh + 3*SMSS;
            sk->state = CA_DISORDER; // 或其他表示快速恢复的状态
        } else if (sk->dup_acks > 3 && sk->state == CA_DISORDER) {
            // 快速恢复期间，每收到一个重复 ACK，cwnd 增加一个 MSS
            sk->cwnd += SMSS;
        }
    } else if (sk->state == CA_DISORDER) {
        // 收到新 ACK，退出快速恢复，进入拥塞避免
        sk->cwnd = sk->ssthresh;
        sk->state = CA_OPEN;
    }
    
    // 4. 更新发送窗口
    update_send_window(sk);
}
```

### 7.3 超时重传处理

```c
void tcp_retransmit_timeout(struct tcp_sock *sk) {
    // 1. 重传最早的未确认报文段
    retransmit_oldest_segment(sk);
    
    // 2. 重置 RTO (通常加倍退避，但此处简化)
    reset_retransmit_timer(sk, RTO * 2);
    
    // 3. 处理拥塞
    sk->ssthresh = max(sk->cwnd/2, 2*SMSS);
    sk->cwnd = 1 * MSS; // 重新开始慢启动
    sk->dup_acks = 0;
}
```

## 8. 安全性与现代扩展

*   **SYN Flood 攻击与防御**：攻击者发送大量伪造源 IP 的 SYN 包，耗尽服务器资源。防御方法包括 **SYN Cookie**：服务器不立即分配资源，而是通过计算生成一个基于源/目的地址、端口和时间的特殊初始序列号（SYN Cookie）。只有收到合法的 ACK 后才分配资源。
*   **TCP 选项**：
    *   **MSS (Maximum Segment Size)**：协商最大报文段长度，避免分片。
    *   **窗口缩放（Window Scale）**：允许窗口字段表示更大的值（最大 2^30 字节），适用于高带宽高延迟网络。
    *   **时间戳（Timestamps）**：更精确的 RTT 测量，防止序列号回绕（PAWS）。
    *   **选择性确认（SACK）**：接收方可以告知发送方具体收到了哪些非连续的数据块，使发送方能更精确地重传丢失的报文段，提高效率。

## 9. 保存路径

本章节内容已根据要求完成，并保存至以下指定目录：
`/docs/network/tcp/TCP_Protocol_Implementation.md`

---
**总结**：TCP 协议通过一套复杂的机制在不可靠的 IP 网络之上实现了可靠传输。理解其状态机、定时器管理、序列号/确认号机制以及流量与拥塞控制算法，是实现一个健壮的 TCP 协议栈的关键。现代网络环境中，还需考虑对安全攻击的防御和对高带宽网络的性能优化（通过选项扩展）。