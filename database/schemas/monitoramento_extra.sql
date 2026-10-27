
-- ============================================================
-- MONITORAMENTO EXTRA
-- Schema independente do monitoramento original
-- ============================================================

CREATE TABLE IF NOT EXISTS candidatos (
    id SERIAL PRIMARY KEY,
    profile_padronizado VARCHAR(255) NOT NULL,
    cargo VARCHAR(50),
    tipo_entidade VARCHAR(50) NOT NULL DEFAULT 'candidato',

    CONSTRAINT uq_entidade_identidade
        UNIQUE NULLS NOT DISTINCT (
            profile_padronizado,
            cargo,
            tipo_entidade
        )
);


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
    status_importacao VARCHAR(20) NOT NULL DEFAULT 'PENDENTE',
    data_processamento TIMESTAMP,
    mensagem_erro TEXT,

    CONSTRAINT uq_coletas_periodo
        UNIQUE NULLS NOT DISTINCT (
            grupo,
            subgrupo,
            data_inicio,
            data_fim
        ),

    CONSTRAINT chk_coletas_status
        CHECK (
            status_importacao IN (
                'PENDENTE',
                'PROCESSANDO',
                'CONCLUIDA',
                'ERRO'
            )
        )
);


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

    CONSTRAINT uq_metricas_perfil_coleta
        UNIQUE (perfil_id, coleta_id)
);


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

    CONSTRAINT uq_post_message
        UNIQUE (message_id)
);


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

    CONSTRAINT uq_metricas_post_coleta
        UNIQUE (post_id, coleta_id)
);


-- ============================================================
-- ÍNDICES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_extra_candidatos_cargo
    ON candidatos(cargo);

CREATE INDEX IF NOT EXISTS idx_extra_candidatos_tipo
    ON candidatos(tipo_entidade);

CREATE INDEX IF NOT EXISTS idx_extra_perfis_candidato
    ON perfis_sociais(candidato_id);

CREATE INDEX IF NOT EXISTS idx_extra_perfis_profile_id
    ON perfis_sociais(profile_id);

CREATE INDEX IF NOT EXISTS idx_extra_coletas_datas
    ON coletas(data_inicio, data_fim);

CREATE INDEX IF NOT EXISTS idx_extra_coletas_grupo
    ON coletas(grupo);

CREATE INDEX IF NOT EXISTS idx_extra_metricas_perfil_perfil
    ON metricas_perfil(perfil_id);

CREATE INDEX IF NOT EXISTS idx_extra_metricas_perfil_coleta
    ON metricas_perfil(coleta_id);

CREATE INDEX IF NOT EXISTS idx_extra_posts_perfil
    ON posts(perfil_id);

CREATE INDEX IF NOT EXISTS idx_extra_metricas_posts_post
    ON metricas_posts(post_id);

CREATE INDEX IF NOT EXISTS idx_extra_metricas_posts_coleta
    ON metricas_posts(coleta_id);
