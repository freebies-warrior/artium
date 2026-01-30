CREATE OR REPLACE FUNCTION items_set_status_from_time()
RETURNS trigger
AS $$
BEGIN
    -- Never auto-change cancelled items
    IF NEW.status = 'cancelled' THEN
        RETURN NEW;
    END IF;

    -- Basic sanity
    IF NEW.time_start IS NULL OR NEW.time_end IS NULL THEN
        RAISE EXCEPTION 'time_start and time_end must be set';
    END IF;

    IF NEW.time_end < NEW.time_start THEN
        RAISE EXCEPTION 'time_end must be >= time_start';
    END IF;

    -- Compute status using DB time
    IF now() < NEW.time_start THEN
        NEW.status := 'draft';
    ELSIF now() < NEW.time_end THEN
        NEW.status := 'active';
    ELSE
        NEW.status := 'ended';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
