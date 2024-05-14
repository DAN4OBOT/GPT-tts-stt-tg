def check_token_limits(user_id, db):
    tokens_used = db.get_tokens_used(user_id)
    token_limit = 1000 
    return tokens_used < token_limit

def check_block_limits(user_id, db):
    blocks_used = db.get_blocks_used(user_id)
    block_limit = 100 
    return blocks_used < block_limit

def check_char_limits(user_id, db):
    chars_used = db.get_chars_used(user_id)
    char_limit = 10000 
    return chars_used < char_limit
