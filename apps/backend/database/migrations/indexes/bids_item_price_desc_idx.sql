CREATE INDEX IF NOT EXISTS bids_item_price_desc_idx
ON bids (item_id, price DESC);
