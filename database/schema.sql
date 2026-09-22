-- ============================================================
-- OBSERVATÓRIO DE REDES SOCIAIS
-- Schema do banco de dados
-- ============================================================


-- ============================================================
-- 1. CANDIDATOS
-- ============================================================

CREATE TABLE IF NOT EXISTS candidatos (
    id SERIAL PRIMARY KEY,

    profile_padronizado VARCHAR(255) NOT NULL,

    cargo VARCHAR(50) NOT NULL,

    UNIQUE (profile_padronizado, cargo)
);


-- ============================================================
-- 2. PERFIS SOCIAIS
-- ============================================================

CREATE TABLE IF NOT EXISTS perfis_sociais (
    id SERIAL PRIMARY KEY,

    candidato_id INTEGER NOT NULL,

    profile VARCHAR(255),
    network VARCHAR(100) NOT NULL,
    profile_id VARCHAR(100),
    link TEXT,

    CONSTRAINT fk_perfil_candidato
        FOREIGN KEY (candidato_id)
        REFERENCES candidatos(id)
        ON DELETE CASCADE,

    CONSTRAINT uq_profile_network
        UNIQUE (profile_id, network)
);


-- ============================================================
-- 3. COLETAS
-- ============================================================

CREATE TABLE IF NOT EXISTS coletas (
    id SERIAL PRIMARY KEY,

    grupo VARCHAR(100) NOT NULL,
    subgrupo VARCHAR(255),

    semana INTEGER,

    data_inicio DATE NOT NULL,
    data_fim DATE NOT NULL,

    benchmarking_arquivo TEXT,
    content_arquivo TEXT,

    data_importacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_coletas_periodo
        UNIQUE NULLS NOT DISTINCT (
            grupo,
            subgrupo,
            data_inicio,
            data_fim
        )
);


-- ============================================================
-- 4. MÉTRICAS DOS PERFIS
-- ============================================================

CREATE TABLE IF NOT EXISTS metricas_perfil (
    id SERIAL PRIMARY KEY,

    perfil_id INTEGER NOT NULL,
    coleta_id INTEGER NOT NULL,

    seguidores BIGINT,
    numero_posts BIGINT,

    likes BIGINT,
    comentarios BIGINT,

    taxa_interacao DOUBLE PRECISION,
    alcance_dia DOUBLE PRECISION,
    page_performance_index DOUBLE PRECISION,

    reacoes_comentarios_compartilhamentos BIGINT,
    visualizacoes_perfil BIGINT,

    external_links TEXT,
    image_link TEXT,

    CONSTRAINT fk_metricas_perfil
        FOREIGN KEY (perfil_id)
        REFERENCES perfis_sociais(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_metricas_coleta
        FOREIGN KEY (coleta_id)
        REFERENCES coletas(id)
        ON DELETE CASCADE,

    UNIQUE (
        perfil_id,
        coleta_id
    )
);


-- ============================================================
-- 5. POSTS
-- ============================================================

CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,

    perfil_id INTEGER NOT NULL,

    message_id VARCHAR(255),

    data TIMESTAMP,

    message TEXT,

    link TEXT,
    external_links TEXT,
    image_link TEXT,

    CONSTRAINT fk_post_perfil
        FOREIGN KEY (perfil_id)
        REFERENCES perfis_sociais(id)
        ON DELETE CASCADE,

    UNIQUE (message_id)
);


-- ============================================================
-- 6. MÉTRICAS DOS POSTS
-- ============================================================

CREATE TABLE IF NOT EXISTS metricas_posts (
    id SERIAL PRIMARY KEY,

    post_id INTEGER NOT NULL,
    coleta_id INTEGER NOT NULL,

    likes BIGINT,
    comentarios BIGINT,
    reacoes_comentarios_compartilhamentos BIGINT,

    taxa_interacao DOUBLE PRECISION,
    alcance_post DOUBLE PRECISION,

    interacoes_impressao_visualizacao DOUBLE PRECISION,

    sentimento_negativo_comentarios DOUBLE PRECISION,

    CONSTRAINT fk_metricas_post
        FOREIGN KEY (post_id)
        REFERENCES posts(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_metricas_post_coleta
        FOREIGN KEY (coleta_id)
        REFERENCES coletas(id)
        ON DELETE CASCADE,

    UNIQUE (
        post_id,
        coleta_id
    )
);


-- ============================================================
-- 7. ÍNDICES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_candidatos_cargo
    ON candidatos(cargo);


CREATE INDEX IF NOT EXISTS idx_perfis_candidato
    ON perfis_sociais(candidato_id);


CREATE INDEX IF NOT EXISTS idx_perfis_profile_id
    ON perfis_sociais(profile_id);


CREATE INDEX IF NOT EXISTS idx_coletas_datas
    ON coletas(data_inicio, data_fim);


CREATE INDEX IF NOT EXISTS idx_coletas_grupo
    ON coletas(grupo);


CREATE INDEX IF NOT EXISTS idx_metricas_perfil_perfil
    ON metricas_perfil(perfil_id);


CREATE INDEX IF NOT EXISTS idx_metricas_perfil_coleta
    ON metricas_perfil(coleta_id);


CREATE INDEX IF NOT EXISTS idx_posts_perfil
    ON posts(perfil_id);


CREATE INDEX IF NOT EXISTS idx_posts_message_id
    ON posts(message_id);


CREATE INDEX IF NOT EXISTS idx_metricas_posts_post
    ON metricas_posts(post_id);


CREATE INDEX IF NOT EXISTS idx_metricas_posts_coleta
    ON metricas_posts(coleta_id);