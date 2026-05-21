-- HydroScan / Smart Hydrogenation Dashboard
-- Demo data for the team.
-- Safe to run more than once: it does not duplicate users or oils.

USE [ReactorMonitorDB];
GO

-- Password for both demo accounts is: admin123
IF NOT EXISTS (SELECT 1 FROM dbo.users WHERE email = 'admin@reactor.ma')
BEGIN
    INSERT INTO dbo.users (nom, email, password_hash, role, actif)
    VALUES ('Admin', 'admin@reactor.ma', '240be518fabd2724dd0f04e374592a27e0d2e9b1a13fef1cf32242b2c903fbd8', 'admin', 1);
END
GO

IF NOT EXISTS (SELECT 1 FROM dbo.users WHERE email = 'operator@reactor.ma')
BEGIN
    INSERT INTO dbo.users (nom, email, password_hash, role, actif)
    VALUES ('Operateur Demo', 'operator@reactor.ma', '240be518fabd2724dd0f04e374592a27e0d2e9b1a13fef1cf32242b2c903fbd8', 'operator', 1);
END
GO

IF NOT EXISTS (SELECT 1 FROM dbo.huiles WHERE nom = 'Soja')
BEGIN
    INSERT INTO dbo.huiles
    (nom, description, temp_min, temp_opt, temp_max, pression_min, pression_opt, pression_max,
     debit_min, debit_opt, debit_max, duree_min_min, duree_opt_min, duree_max_min, rendement_min, rendement_opt)
    VALUES
    ('Soja', 'Huile de soja utilisee pour une hydrogenation standard. Bon equilibre entre temperature, pression et rendement.',
     150, 180, 300, 2, 4, 6, 15, 30, 50, 75, 90, 120, 80, 88);
END
GO

IF NOT EXISTS (SELECT 1 FROM dbo.huiles WHERE nom = 'Tournesol')
BEGIN
    INSERT INTO dbo.huiles
    (nom, description, temp_min, temp_opt, temp_max, pression_min, pression_opt, pression_max,
     debit_min, debit_opt, debit_max, duree_min_min, duree_opt_min, duree_max_min, rendement_min, rendement_opt)
    VALUES
    ('Tournesol', 'Huile de tournesol avec conditions de reaction proches du fonctionnement industriel continu.',
     145, 175, 295, 2, 3.8, 5.8, 14, 28, 48, 70, 85, 115, 78, 86);
END
GO

IF NOT EXISTS (SELECT 1 FROM dbo.huiles WHERE nom = 'Colza')
BEGIN
    INSERT INTO dbo.huiles
    (nom, description, temp_min, temp_opt, temp_max, pression_min, pression_opt, pression_max,
     debit_min, debit_opt, debit_max, duree_min_min, duree_opt_min, duree_max_min, rendement_min, rendement_opt)
    VALUES
    ('Colza', 'Huile de colza adaptee aux essais avec pression moderee et debit H2 controle.',
     140, 170, 285, 1.8, 3.5, 5.5, 12, 26, 45, 65, 80, 110, 76, 85);
END
GO

IF NOT EXISTS (SELECT 1 FROM dbo.huiles WHERE nom = 'Palme')
BEGIN
    INSERT INTO dbo.huiles
    (nom, description, temp_min, temp_opt, temp_max, pression_min, pression_opt, pression_max,
     debit_min, debit_opt, debit_max, duree_min_min, duree_opt_min, duree_max_min, rendement_min, rendement_opt)
    VALUES
    ('Palme', 'Huile de palme avec seuils plus eleves pour simuler une reaction plus robuste.',
     155, 185, 310, 2.2, 4.2, 6.2, 16, 32, 52, 80, 95, 130, 82, 90);
END
GO
