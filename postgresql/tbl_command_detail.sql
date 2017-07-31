CREATE TABLE meekbot.command_detail (
    active_ind BOOLEAN NOT NULL DEFAULT TRUE,
    command_detail_id BIGSERIAL NOT NULL PRIMARY KEY,
    command_id BIGINT NOT NULL REFERENCES meekbot.commands(command_id),
    detail_name text COLLATE pg_catalog."default" NOT NULL,
    detail_type_cd BIGINT NOT NULL REFERENCES meekbot.code_value(code_value),
    detail_text TEXT COLLATE pg_catalog."default",
    detail_num BIGINT,
    seq INT NOT NULL,
    create_dt_tm timestamptz NOT NULL,
    updt_dt_tm timestamptz NOT NULL DEFAULT now()
)
WITH (
    OIDS = FALSE
)
TABLESPACE meekbot;

ALTER TABLE meekbot.command_detail
    OWNER to "Mike";

COMMENT ON TABLE meekbot.command_detail
    IS 'Details/Variables for commands that have them and their current value.';

COMMENT ON COLUMN meekbot.command_detail.detail_type_cd
    IS 'The type of command detail: counter/quote/raffle';

COMMENT ON COLUMN meekbot.command_detail.detail_name
    IS 'The display from the code_value table for detail_type_cd';

COMMENT ON COLUMN meekbot.command_detail.detail_text
    IS 'The value if the detail type is text';

COMMENT ON COLUMN meekbot.command_detail.detail_num
    IS 'The value if the detail type is a number';

COMMENT ON COLUMN meekbot.command_detail.seq
    IS 'The sequence of output if a command has multiple details';

CREATE INDEX xie1_commands
    ON meekbot.command_detail USING btree
    (command_detail_id)
    TABLESPACE meekbot;

CREATE INDEX xie2_commands
    ON meekbot.command_detail USING btree
    (command_id)
    TABLESPACE meekbot;