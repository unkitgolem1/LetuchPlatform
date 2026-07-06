-- ============================================================
-- Invalida una sesión (la expira inmediatamente)
-- Se llama desde AuthService.logout()
-- ============================================================
CREATE OR REPLACE FUNCTION fn_invalidar_sesion(p_id_sesion UUID)
RETURNS VOID
LANGUAGE plpgsql AS $$
BEGIN
    UPDATE sesiones SET expires_at = NOW() WHERE id = p_id_sesion;
END;
$$;
