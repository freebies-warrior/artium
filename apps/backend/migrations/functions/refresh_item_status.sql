CREATE OR REPLACE FUNCTION refresh_item_status(p_item_id uuid)
RETURNS integer
LANGUAGE plpgsql
AS $$
DECLARE
    v_now timestamptz := now();
    v_new_status item_status;
    v_rows integer := 0;
BEGIN
    SELECT CASE
        WHEN status = 'cancelled'::item_status THEN 'cancelled'::item_status
        WHEN v_now < time_start THEN 'draft'::item_status
        WHEN time_end IS NOT NULL AND v_now >= time_end THEN 'ended'::item_status
        ELSE 'active'::item_status
    END
    INTO v_new_status
    FROM items
    WHERE id = p_item_id;

    UPDATE items
    SET status = v_new_status, updated_at = v_now
    WHERE id = p_item_id
        AND status <> 'cancelled'::item_status
        AND status IS DISTINCT FROM v_new_status;

    GET DIAGNOSTICS v_rows = ROW_COUNT;
    RETURN v_rows;
END;
$$;
