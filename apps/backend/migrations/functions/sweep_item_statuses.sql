CREATE OR REPLACE FUNCTION sweep_item_statuses()
RETURNS TABLE(ended_count integer, activated_count integer)
LANGUAGE plpgsql
AS $$
DECLARE
    v_now timestamptz := now();
    v_ended integer := 0;
    v_activated integer := 0;
BEGIN
    -- End anything whose end time has passed (active->ended AND draft->ended catch-up)
    UPDATE items
    SET status = 'ended', updated_at = v_now
    WHERE status IN ('draft','active')
        AND status <> 'cancelled'
        AND time_end IS NOT NULL
        AND v_now >= time_end;
    GET DIAGNOSTICS v_ended = ROW_COUNT;

    -- Activate drafts that are currently in the active window
    UPDATE items
    SET status = 'active', updated_at = v_now
    WHERE status = 'draft'
        AND status <> 'cancelled'
        AND v_now >= time_start
        AND (time_end IS NULL OR v_now < time_end);
    GET DIAGNOSTICS v_activated = ROW_COUNT;

    ended_count := v_ended;
    activated_count := v_activated;
    RETURN NEXT;
END;
$$;
