def check_token_limits(user_id, db):
    tokens_used = db.get_tokens_used(user_id)
    token_limit = 1000  # Установите подходящий лимит
    return tokens_used < token_limit

def check_block_limits(user_id, db):
    blocks_used = db.get_blocks_used(user_id)
    block_limit = 100  # Установите подходящий лимит
    return blocks_used < block_limit

def check_char_limits(user_id, db):
    chars_used = db.get_chars_used(user_id)
    char_limit = 10000  # Установите подходящий лимит
    return chars_used < char_limit
