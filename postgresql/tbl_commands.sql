CREATE TABLE meekbot.commands (
    active_ind BOOLEAN NOT NULL DEFAULT TRUE,
    command_id BIGSERIAL NOT NULL PRIMARY KEY,
    stream_id BIGINT NOT NULL REFERENCES meekbot.stream(stream_id),
    command_name text COLLATE pg_catalog."default" NOT NULL,
    command_string text COLLATE pg_catalog."default" NOT NULL,
    command_type_cd BIGINT NOT NULL REFERENCES meekbot.code_value(code_value),
    stream_reltn_cd BIGINT NOT NULL,
    cooldown_dur INT NOT NULL,
    cooldown_dur_unit_cd BIGSERIAL,
    create_dt_tm timestamptz NOT NULL,
    updt_dt_tm timestamptz NOT NULL DEFAULT now()
)
WITH (
    OIDS = FALSE
)
TABLESPACE meekbot;

ALTER TABLE meekbot.commands
    OWNER to "Mike";

COMMENT ON TABLE meekbot.commands
    IS 'Commands that can be called by the bot.';

COMMENT ON COLUMN meekbot.commands.command_type_cd
    IS 'The type of command: counter/quote/raffle';

COMMENT ON COLUMN meekbot.commands.command_type_cd
    IS 'The minimum stream relationship needed to execute the command';

COMMENT ON COLUMN meekbot.commands.cooldown_dur
    IS 'The number of duration units between executions of the command';

COMMENT ON COLUMN meekbot.commands.cooldown_dur_unit_cd
    IS 'The time unit for cooldown durations';

CREATE INDEX xie1_commands
    ON meekbot.commands USING btree
    (command_id)
    TABLESPACE meekbot;

CREATE INDEX xie2_commands
    ON meekbot.commands USING btree
    (stream_id)
    TABLESPACE meekbot;