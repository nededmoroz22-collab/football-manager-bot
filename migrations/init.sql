-- Minimal schema for Football Manager MVP

CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  tg_id BIGINT UNIQUE NOT NULL,
  username TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS clubs (
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  league TEXT NOT NULL,
  owner_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
  balance BIGINT DEFAULT 1000000,
  rating INTEGER DEFAULT 1000,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS players (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  position TEXT,
  overall INTEGER,
  club_id INTEGER REFERENCES clubs(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS transfers (
  id SERIAL PRIMARY KEY,
  player_id INTEGER REFERENCES players(id) NOT NULL,
  seller_club_id INTEGER REFERENCES clubs(id) NOT NULL,
  starting_price BIGINT NOT NULL,
  status TEXT DEFAULT 'open',
  expires_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS transfer_offers (
  id SERIAL PRIMARY KEY,
  transfer_id INTEGER REFERENCES transfers(id) NOT NULL,
  buyer_club_id INTEGER REFERENCES clubs(id) NOT NULL,
  amount BIGINT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Seed: small list of clubs (3 leagues, 3 clubs each) — можно редактировать
INSERT INTO clubs (name, league) VALUES
  ('Manchester United', 'Premier League'),
  ('Liverpool', 'Premier League'),
  ('Chelsea', 'Premier League'),
  ('Real Madrid', 'La Liga'),
  ('Barcelona', 'La Liga'),
  ('Atletico Madrid', 'La Liga'),
  ('Bayern Munich', 'Bundesliga'),
  ('Borussia Dortmund', 'Bundesliga'),
  ('RB Leipzig', 'Bundesliga')
ON CONFLICT DO NOTHING;