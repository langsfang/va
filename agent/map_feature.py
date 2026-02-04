import json
from collections import deque, defaultdict

from utils import extract_json

def get_path_features(map_info, current_x, current_y, horizon=6):
    """
    计算从当前位置出发，每个可选子节点的未来路径统计特征。
    
    Args:
        map_info (list): 地图节点列表 (JSON list)
        current_x (int): 当前 x 坐标
        current_y (int): 当前 y 坐标
        horizon (int): 向前看的层数（视野深度），默认看未来6层
        
    Returns:
        list: 包含每个选项详细统计特征的列表
    """
    
    # 1. 构建图索引，方便通过 (x, y) 快速查找节点
    node_map = {}
    for node in map_info:
        node_map[(node['x'], node['y'])] = node
        
    # 符号含义映射 (Mapping for LLM readability)
    symbol_meaning = {
        "M": "Monster",
        "?": "Event",
        "$": "Shop",
        "E": "Elite",
        "R": "Rest Site",
        "T": "Treasure",
        "B": "Boss"
    }

    current_node = node_map.get((current_x, current_y))
    if not current_node:
        return {"error": f"Current node ({current_x}, {current_y}) not found in map data."}

    # 如果没有子节点（到达终点）
    if not current_node['children']:
        return {"info": "End of path reached."}

    analysis_results = []

    # 2. 遍历每一个直接相连的子节点（Immediate Options）
    for child_coords in current_node['children']:
        child_x, child_y = child_coords['x'], child_coords['y']
        child_node = node_map.get((child_x, child_y))
        
        if not child_node:
            continue
            
        # 3. 对该路径进行广度优先搜索 (BFS) 来统计视锥内的节点
        # 我们只统计视野 horizon 内所有 *可达* 的唯一节点
        stats = defaultdict(int)
        visited = set()
        queue = deque([(child_node, 1)]) # (node, current_depth)
        
        # 记录路径上是否有特殊节点
        path_flags = {
            "has_shop": False,
            "has_rest": False,
            "forced_elite": False # 简单判断：如果第一层就是 Elite
        }
        
        if child_node['symbol'] == 'E':
            path_flags['forced_elite'] = True

        while queue:
            curr, depth = queue.popleft()
            curr_pos = (curr['x'], curr['y'])
            
            if curr_pos in visited:
                continue
            visited.add(curr_pos)
            
            # 统计资源
            sym = curr['symbol']
            stats[sym] += 1
            
            # 更新标记
            if sym == '$': path_flags['has_shop'] = True
            if sym == 'R': path_flags['has_rest'] = True
            
            # 如果未达到视野极限，继续探索子节点
            if depth < horizon:
                for grand_child in curr['children']:
                    gc_node = node_map.get((grand_child['x'], grand_child['y']))
                    if gc_node:
                        queue.append((gc_node, depth + 1))
        
        # 4. 格式化输出供 LLM 使用的 Prompt 片段
        # 将统计数据转换为自然语言描述或紧凑的 JSON
        summary_text = []
        for sym, count in stats.items():
            name = symbol_meaning.get(sym, sym)
            summary_text.append(f"{name}: {count}")
            
        option_data = {
            "option_coords": f"({child_x}, {child_y})",
            "next_room_type": symbol_meaning.get(child_node['symbol'], "Unknown"),
            "vision_depth": horizon,
            "reachable_resources": dict(stats), # 原始数据
            "path_summary": f"In the next {horizon} floors, you can reach: " + ", ".join(summary_text),
            "key_features": path_flags
        }
        analysis_results.append(option_data)

    return analysis_results

if __name__ == "__main__":
    import sys
    file_path = sys.argv[1]
    print(f"opening {file_path}")

    with open(file_path, 'r', encoding='utf-8') as file:
        file_content = file.read()

    map_data = extract_json(file_content, "map")
    
    current_pos = (0, 0) 

    features = get_path_features(map_data, current_pos[0], current_pos[1], horizon=5)

    print(f"## Decision Context for Node {current_pos}")
    for i, feat in enumerate(features):
        print(f"\n**Option {i+1} (Target: {feat['option_coords']} - {feat['next_room_type']})**")
        print(f"- **Summary:** {feat['path_summary']}")
        print(f"- **Risk/Reward Flags:** Shop={feat['key_features']['has_shop']}, Rest={feat['key_features']['has_rest']}")
        print(f"- **Raw Stats:** {json.dumps(feat['reachable_resources'])}")
