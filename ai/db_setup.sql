-- 1. Enable the vector math extension (pgvector)
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Create the table that your Python script is looking for
CREATE TABLE ai_users (
  id SERIAL PRIMARY KEY,
  name TEXT,
  -- 1536 dimensions to match the model, Qwen
  embedding VECTOR(1536) 
);

-- 3. Create the matching algorithm function so the Node.js server can use it later
CREATE OR REPLACE FUNCTION match_users_by_id (
  p_user_id INT,
  match_threshold FLOAT,
  match_count INT
)
RETURNS TABLE ( id INT, name TEXT, similarity FLOAT )
LANGUAGE plpgsql
AS $$
DECLARE
  v_embedding VECTOR(1536);
BEGIN
  SELECT embedding INTO v_embedding FROM ai_users WHERE ai_users.id = p_user_id;

  RETURN QUERY
  SELECT
    ai_users.id,
    ai_users.name,
    1 - (ai_users.embedding <=> v_embedding) AS similarity
  FROM ai_users
  WHERE ai_users.id != p_user_id 
    AND 1 - (ai_users.embedding <=> v_embedding) > match_threshold
  ORDER BY ai_users.embedding <=> v_embedding
  LIMIT match_count;
END;
$$;