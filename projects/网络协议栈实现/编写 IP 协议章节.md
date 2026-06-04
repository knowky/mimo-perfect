# 编写 IP 协议章节

**任务**: 网络协议栈实现
**时间**: 2026-06-04T23:14:24.625015

# 网络协议栈实现：IP协议章节

## 1. IP协议概述

### 1.1 IP协议在网络模型中的位置
IP（Internet Protocol）协议工作在OSI模型的网络层（第3层），是TCP/IP协议栈的核心协议之一。IP协议提供无连接、不可靠的数据报传输服务，主要负责将数据包从源主机路由到目的主机。

### 1.2 IP协议的核心特性
- **无连接性**：通信前不需要建立连接，每个数据包独立路由
- **不可靠性**：不保证数据包的顺序、完整性或成功交付
- **分组交换**：数据被分割为数据包进行传输
- **尽力而为**：尽可能传输数据，但不提供质量保证

## 2. IPv4协议详细设计

### 2.1 IPv4数据包结构

```c
/* IPv4头部结构定义 */
struct ipv4_header {
#if defined(__LITTLE_ENDIAN_BITFIELD)
    uint8_t  ihl:4,          /* 首部长度 */
             version:4;      /* 版本 */
#elif defined(__BIG_ENDIAN_BITFIELD)
    uint8_t  version:4,      /* 版本 */
             ihl:4;          /* 首部长度 */
#else
#error  "Please fix <asm/byteorder.h>"
#endif
    uint8_t  tos;            /* 服务类型 */
    uint16_t tot_len;        /* 总长度 */
    uint16_t id;             /* 标识 */
    uint16_t frag_off;       /* 标志 + 片偏移 */
    uint8_t  ttl;            /* 生存时间 */
    uint8_t  protocol;       /* 协议 */
    uint16_t check;          /* 首部校验和 */
    uint32_t saddr;          /* 源IP地址 */
    uint32_t daddr;          /* 目的IP地址 */
    /* 可选字段（如果ihl > 5） */
    uint32_t options[];
};
```

### 2.2 各字段详细说明

#### 版本字段（Version, 4位）
- IPv4固定为4
- IPv6固定为6

#### 首部长度（IHL, 4位）
- 以32位字为单位
- 最小值为5（20字节）
- 最大值为15（60字节）

#### 服务类型（TOS, 8位）
```
+-----+-----+-----+-----+-----+-----+-----+-----+
|  DSCP (6 bits)   |  ECN (2 bits)    |
+-----+-----+-----+-----+-----+-----+-----+-----+
```
- DSCP：区分服务代码点
- ECN：显式拥塞通知

#### 总长度（Total Length, 16位）
- 数据包总字节数（头部+数据）
- 最大值：65535字节

#### 标识（Identification, 16位）
- 用于数据包分片重组
- 同一数据包的所有分片具有相同的标识符

#### 标志位（Flags, 3位）
- 第0位：保留
- 第1位：DF（Don't Fragment），禁止分片
- 第2位：MF（More Fragments），后续还有分片

#### 片偏移（Fragment Offset, 13位）
- 以8字节为单位
- 指示当前分片在原始数据包中的位置

#### 生存时间（TTL, 8位）
- 每经过一个路由器减1
- 防止数据包在网络中无限循环
- 初始值通常为64或128

#### 协议字段（Protocol, 8位）
常见协议号：
- 1: ICMP
- 6: TCP
- 17: UDP
- 2: IGMP
- 89: OSPF

#### 首部校验和（Header Checksum, 16位）
- 仅校验头部
- 每经过一个路由器必须重新计算

## 3. IP协议实现核心模块

### 3.1 数据结构定义

```c
/* IP层核心数据结构 */
struct ip_packet {
    struct list_head list;          /* 链表节点 */
    struct sk_buff *skb;            /* 关联的socket缓冲区 */
    uint32_t src_addr;              /* 源IP地址 */
    uint32_t dst_addr;              /* 目的IP地址 */
    uint8_t  protocol;              /* 上层协议 */
    uint8_t  tos;                   /* 服务类型 */
    uint16_t id;                    /* 标识 */
    uint16_t frag_off;              /* 分片偏移 */
    uint8_t  ttl;                   /* 生存时间 */
    uint32_t route_entry;           /* 路由表项 */
    uint32_t timestamp;             /* 时间戳 */
    uint32_t flags;                 /* 状态标志 */
};

/* IP路由表项 */
struct ip_route {
    uint32_t dest;                  /* 目的网络 */
    uint32_t mask;                  /* 子网掩码 */
    uint32_t gateway;               /* 网关地址 */
    struct net_device *dev;         /* 输出网络设备 */
    uint32_t flags;                 /* 路由标志 */
    uint32_t metric;                /* 路由度量 */
    uint32_t use_count;             /* 使用计数 */
    time_t   last_update;           /* 最后更新时间 */
};

/* 分片缓存结构 */
struct ip_frag_queue {
    struct list_head fragments;     /* 分片链表 */
    uint32_t src_addr;              /* 源地址 */
    uint32_t dst_addr;              /* 目的地址 */
    uint16_t id;                    /* 标识 */
    uint8_t  protocol;              /* 协议 */
    uint8_t  last_in_order;         /* 最后顺序到达的分片 */
    uint16_t expected_size;         /* 预期总大小 */
    time_t   expiration;            /* 过期时间 */
    spinlock_t lock;                /* 自旋锁 */
};
```

### 3.2 IP数据包处理流程

#### 3.2.1 发送路径实现

```c
/* IP层发送函数 */
int ip_send_packet(struct sk_buff *skb, struct dst_entry *dst) {
    struct iphdr *iph;
    struct rtable *rt;
    
    /* 1. 检查是否需要分片 */
    if (skb->len > dst->mtu) {
        if (ip_dont_fragment(skb, dst)) {
            /* 发送ICMP目的地不可达（需要分片但设置了DF标志） */
            icmp_send(skb, ICMP_DEST_UNREACH, ICMP_FRAG_NEEDED, 
                     htonl(dst->mtu));
            kfree_skb(skb);
            return -EMSGSIZE;
        }
        /* 执行分片 */
        return ip_fragment(skb, dst->mtu);
    }
    
    /* 2. 填充IP头部 */
    iph = ip_hdr(skb);
    iph->version = 4;
    iph->ihl = 5;
    iph->tos = skb->priority;
    iph->tot_len = htons(skb->len);
    iph->id = ip_select_id(skb);
    iph->frag_off = 0;
    iph->ttl = sysctl_ip_default_ttl;
    iph->protocol = skb->protocol;
    iph->saddr = skb->dev->ip_addr;
    iph->daddr = dst->dst_addr;
    
    /* 3. 计算首部校验和 */
    ip_send_check(iph);
    
    /* 4. 路由决策 */
    rt = ip_route_output(dst->dst_addr);
    if (IS_ERR(rt)) {
        kfree_skb(skb);
        return PTR_ERR(rt);
    }
    
    /* 5. 传递给链路层 */
    return dst->neigh->output(skb);
}

/* 校验和计算函数 */
uint16_t ip_compute_checksum(const void *buff, int len) {
    uint32_t sum = 0;
    const uint16_t *ptr = buff;
    
    while (len > 1) {
        sum += *ptr++;
        len -= 2;
    }
    
    if (len == 1)
        sum += *(uint8_t *)ptr;
    
    sum = (sum >> 16) + (sum & 0xffff);
    sum += sum >> 16;
    
    return (uint16_t)(~sum);
}
```

#### 3.2.2 接收路径实现

```c
/* IP层接收函数 */
int ip_rcv(struct sk_buff *skb, struct net_device *dev) {
    struct iphdr *iph;
    uint16_t check;
    
    /* 1. 基本验证 */
    if (skb->len < sizeof(struct iphdr))
        goto drop;
    
    iph = ip_hdr(skb);
    
    /* 版本检查 */
    if (iph->version != 4)
        goto drop;
    
    /* 头部长度检查 */
    if (iph->ihl < 5)
        goto drop;
    
    if (skb->len < (iph->ihl << 2))
        goto drop;
    
    /* 2. 校验和验证 */
    check = ip_compute_checksum(iph, iph->ihl << 2);
    if (check != 0)
        goto drop;
    
    /* 3. 验证目的地址 */
    if (!ip_addr_is_local(iph->daddr) && 
        !ip_addr_is_broadcast(iph->daddr, dev))
        goto drop;
    
    /* 4. 处理TTL */
    if (--iph->ttl == 0) {
        icmp_send(skb, ICMP_TIME_EXCEEDED, ICMP_EXC_TTL, 0);
        goto drop;
    }
    
    /* 5. 分片处理 */
    if (iph->frag_off & htons(IP_MF | IP_OFFSET)) {
        skb = ip_defrag(iph, skb);
        if (!skb)
            return 0;  /* 分片缓存中，等待更多分片 */
    }
    
    /* 6. 协议分发 */
    return ip_local_deliver(skb);
    
drop:
    kfree_skb(skb);
    return -1;
}
```

### 3.3 IP分片与重组实现

#### 3.3.1 分片算法实现

```c
/* IP分片函数 */
int ip_fragment(struct sk_buff *skb, uint32_t mtu) {
    struct iphdr *iph = ip_hdr(skb);
    int offset, end, frag_size;
    struct sk_buff *frag;
    
    /* 检查是否允许分片 */
    if (iph->frag_off & htons(IP_DF)) {
        icmp_send(skb, ICMP_DEST_UNREACH, ICMP_FRAG_NEEDED, 
                 htonl(mtu));
        return -EMSGSIZE;
    }
    
    /* 计算最大分片大小（8字节对齐） */
    mtu -= (iph->ihl << 2);
    frag_size = mtu & ~7;
    
    offset = 0;
    end = skb->len - (iph->ihl << 2);
    
    while (offset < end) {
        /* 创建分片skb */
        frag = skb_clone(skb, GFP_ATOMIC);
        if (!frag)
            goto fail;
        
        /* 计算当前分片大小 */
        int frag_len = frag_size;
        if (offset + frag_len >= end)
            frag_len = end - offset;
        
        /* 设置分片偏移 */
        iph = ip_hdr(frag);
        iph->frag_off = htons(offset >> 3);
        if (offset + frag_len < end)
            iph->frag_off |= htons(IP_MF);
        
        /* 调整skb长度 */
        skb_trim(frag, (iph->ihl << 2) + frag_len);
        skb_pull(frag, iph->ihl << 2);
        skb_put(frag, frag_len);
        skb_push(frag, iph->ihl << 2);
        
        /* 重新计算校验和 */
        iph->tot_len = htons(frag->len);
        iph->check = 0;
        iph->check = ip_compute_checksum(iph, iph->ihl << 2);
        
        /* 发送分片 */
        ip_send_packet(frag, frag->dst);
        
        offset += frag_size;
    }
    
    return 0;
    
fail:
    return -ENOMEM;
}
```

#### 3.3.2 重组算法实现

```c
/* IP重组函数 */
struct sk_buff *ip_defrag(struct iphdr *iph, struct sk_buff *skb) {
    struct ip_frag_queue *fq;
    struct sk_buff *prev, *next;
    
    /* 查找或创建重组队列 */
    fq = ip_frag_create_queue(iph);
    if (!fq)
        return NULL;
    
    spin_lock(&fq->lock);
    
    /* 检查是否是最后一个分片 */
    if (!(iph->frag_off & htons(IP_MF))) {
        fq->expected_size = (ntohs(iph->frag_off) << 3) + 
                          (skb->len - (iph->ihl << 2));
    }
    
    /* 将分片插入队列（按偏移排序） */
    prev = NULL;
    list_for_each_entry(next, &fq->fragments, list) {
        struct iphdr *next_hdr = ip_hdr(next);
        if (ntohs(iph->frag_off) < ntohs(next_hdr->frag_off))
            break;
        prev = next;
    }
    
    if (prev)
        list_add(&skb->list, &prev->list);
    else
        list_add(&skb->list, &fq->fragments);
    
    /* 检查是否收集完所有分片 */
    if (ip_frag_is_complete(fq)) {
        /* 重组数据包 */
        skb = ip_frag_reassemble(fq);
        spin_unlock(&fq->lock);
        ip_frag_free_queue(fq);
        return skb;
    }
    
    /* 设置超时定时器 */
    if (!timer_pending(&fq->timer)) {
        fq->timer.expires = jiffies + IP_FRAG_TIME;
        add_timer(&fq->timer);
    }
    
    spin_unlock(&fq->lock);
    return NULL;  /* 等待更多分片 */
}

/* 检查重组是否完成 */
static int ip_frag_is_complete(struct ip_frag_queue *fq) {
    int offset = 0;
    struct sk_buff *skb;
    
    list_for_each_entry(skb, &fq->fragments, list) {
        struct iphdr *iph = ip_hdr(skb);
        
        if (ntohs(iph->frag_off) << 3 != offset)
            return 0;
        
        offset += skb->len - (iph->ihl << 2);
        
        if (!(iph->frag_off & htons(IP_MF)))
            return (fq->expected_size == offset);
    }
    
    return 0;
}
```

### 3.4 IP路由实现

#### 3.4.1 路由表结构与查找

```c
/* 路由表实现 */
struct ip_route_table {
    struct hlist_head hash[RT_HASH_SIZE];
    spinlock_t lock;
    struct timer_list gc_timer;  /* 垃圾回收定时器 */
};

/* 最长前缀匹配算法 */
struct ip_route *ip_route_lookup(uint32_t dest) {
    struct ip_route *best_match = NULL;
    uint32_t best_prefix_len = 0;
    int i;
    
    for (i = 0; i < RT_HASH_SIZE; i++) {
        struct ip_route *rt;
        
        hlist_for_each_entry(rt, &rt_table.hash[i], node) {
            uint32_t prefix_len = 0;
            uint32_t mask = rt->mask;
            
            /* 计算前缀长度 */
            while (mask) {
                prefix_len++;
                mask >>= 1;
            }
            
            /* 检查是否匹配 */
            if ((dest & rt->mask) == rt->dest) {
                if (prefix_len > best_prefix_len) {
                    best_match = rt;
                    best_prefix_len = prefix_len;
                }
            }
        }
    }
    
    return best_match;
}

/* 默认路由查找 */
struct ip_route *ip_route_default(void) {
    return ip_route_lookup(0);
}
```

#### 3.4.2 路由缓存实现

```c
/* 路由缓存实现 */
struct ip_route_cache {
    struct hlist_node node;
    uint32_t dst_addr;
    uint32_t src_addr;
    uint8_t  tos;
    struct ip_route *route;
    uint32_t last_used;
    atomic_t refcnt;
};

/* 路由缓存查找 */
struct ip_route_cache *ip_route_cache_find(uint32_t dst, uint32_t src, 
                                           uint8_t tos) {
    uint32_t hash = ip_route_hash(dst, src, tos);
    struct ip_route_cache *cache;
    
    hlist_for_each_entry(cache, &rt_cache.hash[hash], node) {
        if (cache->dst_addr == dst && 
            cache->src_addr == src &&
            cache->tos == tos) {
            /* 更新最后使用时间 */
            cache->last_used = jiffies;
            atomic_inc(&cache->refcnt);
            return cache;
        }
    }
    
    return NULL;
}

/* 路由缓存更新 */
void ip_route_cache_update(uint32_t dst, uint32_t src, uint8_t tos,
                          struct ip_route *rt) {
    struct ip_route_cache *cache;
    uint32_t hash;
    
    /* 检查是否已存在 */
    cache = ip_route_cache_find(dst, src, tos);
    if (cache) {
        /* 更新现有条目 */
        cache->route = rt;
        cache->last_used = jiffies;
        return;
    }
    
    /* 创建新缓存条目 */
    cache = kmalloc(sizeof(*cache), GFP_ATOMIC);
    if (!cache)
        return;
    
    cache->dst_addr = dst;
    cache->src_addr = src;
    cache->tos = tos;
    cache->route = rt;
    cache->last_used = jiffies;
    atomic_set(&cache->refcnt, 1);
    
    hash = ip_route_hash(dst, src, tos);
    hlist_add_head(&cache->node, &rt_cache.hash[hash]);
}
```

## 4. IPv6协议扩展实现

### 4.1 IPv6头部结构

```c
/* IPv6头部结构 */
struct ipv6_header {
    uint32_t version:4,        /* 版本 */
             traffic_class:8,  /* 流量类别 */
             flow_label:20;    /* 流标签 */
    uint16_t payload_len;      /* 有效载荷长度 */
    uint8_t  next_header;      /* 下一个头部 */
    uint8_t  hop_limit;        /* 跳数限制 */
    struct in6_addr src_addr;  /* 源地址（128位） */
    struct in6_addr dst_addr;  /* 目的地址（128位） */
};
```

### 4.2 IPv6与IPv4的主要区别实现

```c
/* IPv6处理与IPv4的区别 */

/* 1. 无校验和计算（依赖上层校验） */
void ipv6_send_check(struct sk_buff *skb) {
    /* IPv6头部不包含校验和字段 */
    /* 现代网络接口卡通常支持校验和卸载 */
    if (skb->dev->features & NETIF_F_IPV6_CSUM) {
        skb->ip_summed = CHECKSUM_PARTIAL;
        skb->csum_start = skb_headroom(skb) + 
                         offsetof(struct ipv6hdr, nexthdr);
        skb->csum_offset = 0;  /* 无校验和字段 */
    }
}

/* 2. 扩展头部处理 */
int ipv6_parse_ext_headers(struct sk_buff *skb, struct ipv6hdr *iph) {
    uint8_t nexthdr = iph->nexthdr;
    int offset = sizeof(struct ipv6hdr);
    
    while (ipv6_is_ext_hdr(nexthdr)) {
        struct ipv6_opt_hdr *ext_hdr;
        
        /* 检查是否有足够的空间 */
        if (skb->len < offset + sizeof(struct ipv6_opt_hdr))
            return -EINVAL;
        
        ext_hdr = (struct ipv6_opt_hdr *)(skb->data + offset);
        
        /* 处理特定扩展头部 */
        switch (nexthdr) {
        case IPPROTO_HOPOPTS:
            offset += ipv6_parse_hopopts(skb, ext_hdr);
            break;
        case IPPROTO_ROUTING:
            offset += ipv6_parse_routing(skb, ext_hdr);
            break;
        case IPPROTO_FRAGMENT:
            offset += ipv6_parse_fragment(skb, ext_hdr);
            break;
        case IPPROTO_DSTOPTS:
            offset += ipv6_parse_dstopts(skb, ext_hdr);
            break;
        default:
            return nexthdr;  /* 返回下一个协议 */
        }
        
        nexthdr = ext_hdr->nexthdr;
    }
    
    return nexthdr;
}

/* 3. 无分片标志处理 */
bool ipv6_can_fragment(struct sk_buff *skb) {
    /* IPv6在路径MTU发现方面更严格 */
    struct rt6_info *rt = (struct rt6_info *)skb->dst;
    
    /* 检查是否支持分片 */
    if (!(rt->rt6i_flags & RTF_NONEXTHOP) &&
        ipv6_addr_is_multicast(&ipv6_hdr(skb)->daddr)) {
        return false;  /* 多播通常不允许分片 */
    }
    
    return true;
}
```

## 5. 关键实现要点与最佳实践

### 5.1 性能优化策略

#### 5.1.1 快速路径优化
```c
/* 快速路径优化示例 */
static int ip_fast_path(struct sk_buff *skb) {
    struct iphdr *iph;
    
    /* 快速路径只处理最简单的情况 */
    iph = ip_hdr(skb);
    
    if (iph->ihl == 5 &&                    /* 无IP选项 */
        !(iph->frag_off & htons(IP_MF | IP_OFFSET)) &&  /* 无分片 */
        iph->ttl > 1 &&                     /* TTL > 1 */
        !ip_is_fragmented(iph) &&           /* 未分片 */
        ip_local_deliver_fast(skb)) {       /* 本地快速交付 */
        
        /* 更新统计信息 */
        IP_INC_STATS_BH(IP_MIB_INDELIVERS);
        return NET_RX_SUCCESS;
    }
    
    return -1;  /* 进入慢速路径 */
}
```

#### 5.1.2 内存池管理
```c
/* IP数据包内存池 */
struct ip_packet_pool {
    struct kmem_cache *cache;
    spinlock_t lock;
    int allocated;
    int free;
};

/* 从内存池分配IP数据包 */
struct sk_buff *ip_alloc_skb(gfp_t gfp_mask) {
    struct sk_buff *skb;
    
    /* 首先尝试从内存池分配 */
    spin_lock(&ip_pool.lock);
    if (ip_pool.free > 0) {
        skb = kmem_cache_alloc(ip_pool.cache, GFP_ATOMIC);
        if (skb) {
            ip_pool.free--;
            ip_pool.allocated++;
        }
    } else {
        /* 内存池为空，从系统分配 */
        skb = alloc_skb(MAX_IP_PACKET_SIZE, gfp_mask);
    }
    spin_unlock(&ip_pool.lock);
    
    return skb;
}
```

### 5.2 安全性考虑

#### 5.2.1 IP欺骗防护
```c
/* IP欺骗检测 */
bool ip_spoofing_check(struct sk_buff *skb) {
    struct iphdr *iph = ip_hdr(skb);
    struct net_device *dev = skb->dev;
    
    /* 检查源地址是否合法 */
    if (iph->saddr == 0 || 
        iph->saddr == 0xFFFFFFFF) {
        IP_INC_STATS_BH(IP_MIB_INADDRERRORS);
        return false;
    }
    
    /* 检查反向路径过滤（uRPF） */
    if (sysctl_ip_rp_filter) {
        struct ip_route *rt = ip_route_output(iph->saddr);
        if (IS_ERR(rt) || rt->dev != dev) {
            IP_INC_STATS_BH(IP_MIB_INADDRERRORS);
            return false;
        }
    }
    
    /* 检查是否使用私有地址作为源地址 */
    if (ip_is_private(iph->saddr) && 
        !ip_addr_is_local(iph->saddr)) {
        /* 记录日志但允许通过（配置可选） */
        if (sysctl_log_martians)
            net_warn_ratelimited("martian source %pI4 from %pI4, dev %s\n",
                                &iph->saddr, &iph->daddr, dev->name);
    }
    
    return true;
}
```

#### 5.2.2 数据包过滤
```c
/* IP层访问控制列表 */
struct ip_acl {
    struct list_head list;
    uint32_t src_addr;
    uint32_t src_mask;
    uint32_t dst_addr;
    uint32_t dst_mask;
    uint8_t  protocol;
    uint16_t src_port;
    uint16_t dst_port;
    uint8_t  action;      /* 允许/拒绝 */
    uint32_t hit_count;
};

/* ACL检查函数 */
bool ip_acl_check(struct sk_buff *skb) {
    struct iphdr *iph = ip_hdr(skb);
    struct ip_acl *acl;
    
    list_for_each_entry(acl, &ip_acl_list, list) {
        if ((iph->saddr & acl->src_mask) == acl->src_addr &&
            (iph->daddr & acl->dst_mask) == acl->dst_addr &&
            (acl->protocol == 0 || iph->protocol == acl->protocol)) {
            
            acl->hit_count++;
            
            if (acl->action == IP_ACL_DENY) {
                IP_INC_STATS_BH(IP_MIB_INDISCARDS);
                return false;
            }
            return true;  /* 允许 */
        }
    }
    
    return true;  /* 默认允许 */
}
```

### 5.3 调试与监控接口

```c
/* IP层统计信息 */
struct ip_statistics {
    /* 收包统计 */
    uint32_t in_receives;
    uint32_t in_hdr_errors;
    uint32_t in_addr_errors;
    uint32_t in_discards;
    uint32_t in_delivers;
    
    /* 发包统计 */
    uint32_t out_requests;
    uint32_t out_discards;
    uint32_t out_no_routes;
    uint32_t out_transmits;
    
    /* 分片统计 */
    uint32_t reasm_timeout;
    uint32_t reasm_reqds;
    uint32_t reasm_oks;
    uint32_t reasm_fails;
    
    /* 分片统计 */
    uint32_t frag_oks;
    uint32_t frag_fails;
    uint32_t frag_creates;
};

/* 通过proc文件系统暴露统计信息 */
static int ip_proc_show(struct seq_file *m, void *v) {
    struct ip_statistics *stats = &ip_stats;
    
    seq_printf(m, "Ip:\n");
    seq_printf(m, "    %u InReceives\n", stats->in_receives);
    seq_printf(m, "    %u InHdrErrors\n", stats->in_hdr_errors);
    seq_printf(m, "    %u InAddrErrors\n", stats->in_addr_errors);
    seq_printf(m, "    %u InDiscards\n", stats->in_discards);
    seq_printf(m, "    %u InDelivers\n", stats->in_delivers);
    seq_printf(m, "    %u OutRequests\n", stats->out_requests);
    seq_printf(m, "    %u OutDiscards\n", stats->out_discards);
    seq_printf(m, "    %u OutNoRoutes\n", stats->out_no_routes);
    seq_printf(m, "    %u ReasmTimeout\n", stats->reasm_timeout);
    seq_printf(m, "    %u ReasmReqds\n", stats->reasm_reqds);
    seq_printf(m, "    %u ReasmOKs\n", stats->reasm_oks);
    seq_printf(m, "    %u ReasmFails\n", stats->reasm_fails);
    seq_printf(m, "    %u FragOKs\n", stats->frag_oks);
    seq_printf(m, "    %u FragFails\n", stats->frag_fails);
    seq_printf(m, "    %u FragCreates\n", stats->frag_creates);
    
    return 0;
}
```

## 6. 测试与验证

### 6.1 单元测试用例

```c
/* IP协议单元测试 */
static void test_ip_header_parse(void) {
    struct sk_buff *skb;
    struct iphdr *iph;
    
    /* 创建测试数据包 */
    skb = alloc_skb(100, GFP_KERNEL);
    skb_put(skb, 100);
    
    /* 填充IP头部 */
    iph = (struct iphdr *)skb->data;
    iph->version = 4;
    iph->ihl = 5;
    iph->tot_len = htons(100);
    iph->ttl = 64;
    iph->protocol = IPPROTO_TCP;
    iph->saddr = htonl(0xC0A80001);  /* 192.168.0.1 */
    iph->daddr = htonl(0xC0A80002);  /* 192.168.0.2 */
    iph->check = 0;
    iph->check = ip_compute_checksum(iph, sizeof(struct iphdr));
    
    /* 测试解析 */
    ASSERT(ip_rcv(skb, NULL) == 0);
    
    /* 验证统计信息 */
    ASSERT(ip_stats.in_receives == 1);
    ASSERT(ip_stats.in_delivers == 1);
    
    kfree_skb(skb);
}

/* 分片重组测试 */
static void test_ip_fragment_reassembly(void) {
    struct sk_buff *skb1, *skb2, *skb3;
    struct sk_buff *reassembled;
    
    /* 创建三个分片 */
    skb1 = create_fragment(0, 64, true);   /* 偏移0，MF=1 */
    skb2 = create_fragment(64, 64, true);  /* 偏移64，MF=1 */
    skb3 = create_fragment(128, 32, false); /* 偏移128，MF=0 */
    
    /* 模拟接收 */
    reassembled = ip_defrag(ip_hdr(skb1), skb1);
    ASSERT(reassembled == NULL);  /* 还未完成 */
    
    reassembled = ip_defrag(ip_hdr(skb2), skb2);
    ASSERT(reassembled == NULL);  /* 还未完成 */
    
    reassembled = ip_defrag(ip_hdr(skb3), skb3);
    ASSERT(reassembled != NULL);  /* 重组完成 */
    
    /* 验证重组结果 */
    ASSERT(reassembled->len == 160);  /* 总长度160 */
    
    kfree_skb(skb1);
    kfree_skb(skb2);
    kfree_skb(skb3);
    kfree_skb(reassembled);
}
```

### 6.2 集成测试场景

```c
/* 路由集成测试 */
static void test_routing_integration(void) {
    struct net_device *dev1, *dev2;
    struct sk_buff *skb;
    
    /* 创建两个网络设备 */
    dev1 = create_netdev("eth0", 0xC0A80001);  /* 192.168.0.1 */
    dev2 = create_netdev("eth1", 0xC0A80101);  /* 192.168.1.1 */
    
    /* 配置路由表 */
    ip_route_add(0xC0A80000, 0xFFFFFF00, 0, dev1);  /* 192.168.0.0/24 */
    ip_route_add(0xC0A80100, 0xFFFFFF00, 0, dev2);  /* 192.168.1.0/24 */
    ip_route_add(0, 0, 0xC0A80001, dev1);           /* 默认路由 */
    
    /* 测试本地发送 */
    skb = create_test_packet(0xC0A80002, 0xC0A80001, 100);
    ASSERT(ip_send_packet(skb, NULL) == 0);
    ASSERT(dev1->tx_count == 1);
    
    /* 测试跨网段发送 */
    skb = create_test_packet(0xC0A80002, 0xC0A80102, 100);
    ASSERT(ip_send_packet(skb, NULL) == 0);
    ASSERT(dev1->tx_count == 2);  /* 通过默认路由 */
    
    /* 测试直接路由 */
    skb = create_test_packet(0xC0A80002, 0xC0A80003, 100);
    ASSERT(ip_send_packet(skb, NULL) == 0);
    ASSERT(dev1->tx_count == 3);
    
    /* 清理 */
    destroy_netdev(dev1);
    destroy_netdev(dev2);
}
```

## 7. 部署与配置建议

### 7.1 内核参数调优

```bash
# /etc/sysctl.conf 中的相关参数

# IP转发（路由器必需）
net.ipv4.ip_forward = 1

# 反向路径过滤（防IP欺骗）
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# 记录火星包（异常数据包）
net.ipv4.conf.all.log_martians = 1

# 禁用ICMP重定向（安全考虑）
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0

# 调整ARP表大小
net.ipv4.neigh.default.gc_thresh1 = 256
net.ipv4.neigh.default.gc_thresh2 = 1024
net.ipv4.neigh.default.gc_thresh3 = 2048

# 调整路由缓存
net.ipv4.route.max_size = 524288
net.ipv4.route.gc_thresh = 524288
net.ipv4.route.gc_timeout = 60

# 调整IP分片