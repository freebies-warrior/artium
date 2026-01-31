DROP TRIGGER IF EXISTS trg_items_set_status_from_time ON items;

CREATE TRIGGER trg_items_set_status_from_time
BEFORE INSERT OR UPDATE OF time_start, time_end, status
ON items
FOR EACH ROW
EXECUTE FUNCTION items_set_status_from_time();