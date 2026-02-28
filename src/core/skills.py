

# Skill: 跨域信息关联能力，实现不同来源信息的智能关联匹配
def cross_domain_information_association(information_sources: list, association_rules: dict = None) -> dict:
    """
    跨域信息关联功能
    :param information_sources: 不同域的信息来源列表
    :param association_rules: 关联规则字典，为空时使用默认规则
    :return: 关联后的结构化信息字典
    """
    if association_rules is None:
        association_rules = {
            "time_match_threshold": 3600,
            "content_similarity_threshold": 0.7
        }
    
    result = {
        "associated_groups": [],
        "unassociated_items": [],
        "association_count": 0
    }
    
    # 基础关联逻辑实现
    seen_items = set()
    for idx, item in enumerate(information_sources):
        if idx in seen_items:
            continue
        group = [item]
        seen_items.add(idx)
        
        for j in range(idx + 1, len(information_sources)):
            if j in seen_items:
                continue
            other_item = information_sources[j]
            # 简单相似度判断
            similarity = 0.8 if len(set(str(item).split()) & set(str(other_item).split())) > 3 else 0.3
            if similarity >= association_rules["content_similarity_threshold"]:
                group.append(other_item)
                seen_items.add(j)
        
        if len(group) > 1:
            result["associated_groups"].append(group)
            result["association_count"] += 1
        else:
            result["unassociated_items"].append(item)
    
    return result


# Skill: 跨域信息关联能力，实现不同来源信息的智能关联匹配
def cross_domain_information_association(information_sources: list, association_rules: dict = None, association_threshold: float = 0.7) -> list:
    """
    跨域信息关联功能
    :param information_sources: 不同域的信息来源列表
    :param association_rules: 关联规则字典，为空时使用默认规则
    :param association_threshold: 关联相似度阈值，默认0.7
    :return: 关联后的分组列表
    """
    if association_rules is None:
        association_rules = {
            "time_match_threshold": 3600,
            "content_similarity_threshold": association_threshold
        }
    
    groups = []
    seen_items = set()
    
    for idx, item in enumerate(information_sources):
        if idx in seen_items:
            continue
        current_group = [item]
        seen_items.add(idx)
        
        for j in range(idx + 1, len(information_sources)):
            if j in seen_items:
                continue
            other_item = information_sources[j]
            
            # 计算内容相似度
            item_embedding = item.get('embedding', [])
            other_embedding = other_item.get('embedding', [])
            similarity = 0.0
            if item_embedding and other_embedding and len(item_embedding) == len(other_embedding):
                # 简单余弦相似度计算
                dot_product = sum(a*b for a,b in zip(item_embedding, other_embedding))
                norm_a = sum(a*a for a in item_embedding) ** 0.5
                norm_b = sum(a*a for a in other_embedding) ** 0.5
                if norm_a and norm_b:
                    similarity = dot_product / (norm_a * norm_b)
            
            if similarity >= association_threshold:
                current_group.append(other_item)
                seen_items.add(j)
        
        groups.append(current_group)
    
    return groups
