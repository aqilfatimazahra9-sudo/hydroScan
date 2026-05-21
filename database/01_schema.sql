-- HydroScan / Smart Hydrogenation Dashboard
-- Portable SQL Server schema for the team.
-- Safe to run: it creates missing database/tables without using local .mdf paths.

USE [master];
GO

IF DB_ID(N'ReactorMonitorDB') IS NULL
BEGIN
    CREATE DATABASE [ReactorMonitorDB];
END
GO

USE [ReactorMonitorDB];
GO

IF OBJECT_ID(N'dbo.users', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.users (
        id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        nom NVARCHAR(100) NOT NULL,
        email NVARCHAR(150) NOT NULL UNIQUE,
        password_hash NVARCHAR(255) NOT NULL,
        role NVARCHAR(50) NOT NULL CONSTRAINT DF_users_role DEFAULT ('operator'),
        actif BIT NOT NULL CONSTRAINT DF_users_actif DEFAULT (1),
        created_at DATETIME NOT NULL CONSTRAINT DF_users_created_at DEFAULT (GETDATE())
    );
END
GO

IF OBJECT_ID(N'dbo.huiles', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.huiles (
        id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        nom NVARCHAR(100) NOT NULL,
        description NVARCHAR(500) NULL,
        temp_min FLOAT NOT NULL,
        temp_opt FLOAT NOT NULL,
        temp_max FLOAT NOT NULL,
        pression_min FLOAT NOT NULL,
        pression_opt FLOAT NOT NULL,
        pression_max FLOAT NOT NULL,
        debit_min FLOAT NOT NULL,
        debit_opt FLOAT NOT NULL,
        debit_max FLOAT NOT NULL,
        duree_min_min INT NOT NULL,
        duree_opt_min INT NOT NULL,
        duree_max_min INT NOT NULL,
        rendement_min FLOAT NOT NULL,
        rendement_opt FLOAT NOT NULL,
        created_at DATETIME NOT NULL CONSTRAINT DF_huiles_created_at DEFAULT (GETDATE())
    );
END
GO

IF OBJECT_ID(N'dbo.sessions_reacteur', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.sessions_reacteur (
        id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        user_id INT NOT NULL,
        huile_id INT NOT NULL,
        debut DATETIME NOT NULL CONSTRAINT DF_sessions_debut DEFAULT (GETDATE()),
        fin DATETIME NULL,
        statut NVARCHAR(50) NOT NULL CONSTRAINT DF_sessions_statut DEFAULT ('en_cours'),
        notes NVARCHAR(1000) NULL,
        lim_temp_min FLOAT NULL,
        lim_temp_opt FLOAT NULL,
        lim_temp_max FLOAT NULL,
        lim_pression_min FLOAT NULL,
        lim_pression_opt FLOAT NULL,
        lim_pression_max FLOAT NULL,
        lim_debit_min FLOAT NULL,
        lim_debit_opt FLOAT NULL,
        lim_debit_max FLOAT NULL,
        lim_duree_min INT NULL,
        lim_duree_opt INT NULL,
        lim_duree_max INT NULL,
        lim_rendement_min FLOAT NULL,
        lim_rendement_opt FLOAT NULL,
        CONSTRAINT FK_sessions_users FOREIGN KEY (user_id) REFERENCES dbo.users(id),
        CONSTRAINT FK_sessions_huiles FOREIGN KEY (huile_id) REFERENCES dbo.huiles(id)
    );
END
GO

IF OBJECT_ID(N'dbo.mesures_reacteur', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.mesures_reacteur (
        id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        session_id INT NOT NULL,
        timestamp DATETIME NOT NULL CONSTRAINT DF_mesures_timestamp DEFAULT (GETDATE()),
        temperature FLOAT NOT NULL,
        pression FLOAT NOT NULL,
        debit_h2 FLOAT NOT NULL,
        rendement FLOAT NULL,
        statut_global NVARCHAR(20) NOT NULL CONSTRAINT DF_mesures_statut DEFAULT ('normal'),
        CONSTRAINT FK_mesures_sessions FOREIGN KEY (session_id) REFERENCES dbo.sessions_reacteur(id)
    );
END
GO

IF OBJECT_ID(N'dbo.alertes', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.alertes (
        id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        session_id INT NOT NULL,
        timestamp DATETIME NOT NULL CONSTRAINT DF_alertes_timestamp DEFAULT (GETDATE()),
        type_alerte NVARCHAR(100) NOT NULL,
        parametre NVARCHAR(50) NOT NULL,
        valeur_lue FLOAT NOT NULL,
        valeur_seuil FLOAT NOT NULL,
        niveau NVARCHAR(20) NOT NULL,
        message NVARCHAR(500) NULL,
        resolue BIT NOT NULL CONSTRAINT DF_alertes_resolue DEFAULT (0),
        resolue_at DATETIME NULL,
        CONSTRAINT FK_alertes_sessions FOREIGN KEY (session_id) REFERENCES dbo.sessions_reacteur(id)
    );
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'idx_mesures_session' AND object_id = OBJECT_ID(N'dbo.mesures_reacteur'))
BEGIN
    CREATE NONCLUSTERED INDEX idx_mesures_session
    ON dbo.mesures_reacteur (session_id ASC, timestamp DESC);
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'idx_alertes_session' AND object_id = OBJECT_ID(N'dbo.alertes'))
BEGIN
    CREATE NONCLUSTERED INDEX idx_alertes_session
    ON dbo.alertes (session_id ASC, resolue ASC, timestamp DESC);
END
GO
