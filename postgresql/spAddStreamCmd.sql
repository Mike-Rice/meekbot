CREATE OR REPLACE FUNCTION meekbot.addStreamCmd(streamID bigint, reltn text, cooldown int, cmd_name text, cmd_text text
                                                ,cmd_type text)
RETURNS bigint AS $CMD$
DECLARE
 relationship_cd bigint := 0;
 cmdID bigint := 0;
 second_cd bigint := 0;
 cmd_type_cd bigint := 0;
BEGIN

  --Get command type code
SELECT
  code_value.code_value INTO cmd_type_cd
FROM
  meekbot.code_value
WHERE code_set = 3
  AND display_key = cmd_type
  AND active_ind = TRUE;

  --Get the relationship code
 SELECT
   code_value.code_value INTO relationship_cd
 FROM meekbot.code_value
 WHERE code_set = 1
   AND display_key = reltn
   AND active_ind = TRUE;

  --Get the code value for seconds
  SELECT
   code_value.code_value INTO second_cd
 FROM meekbot.code_value
 WHERE code_set = 2
   AND display_key = 'SECOND'
   AND active_ind = TRUE;

  SELECT
    commands.command_id INTO cmdID
  FROM meekbot.commands
  WHERE stream_id = streamID
    AND command_name = cmd_name
    AND active_ind = TRUE;

 -- ADD LOGIC TO GET INACTIVE COMMANDS OF THE SAME NAME IF THEY EXIST

 --Add logic to see if command already exists and return a negative value if so
 IF cmdID IS NULL THEN
   INSERT INTO meekbot.commands(stream_id
                              , stream_reltn_cd
                              , cooldown_dur
                              , cooldown_dur_unit_cd
                              , command_name
                              , command_string
                              , command_type_cd
                              , create_dt_tm)
   VALUES (streamID, relationship_cd, cooldown, second_cd, cmd_name, cmd_text, cmd_type_cd, now())
   RETURNING commands.command_id INTO cmdID;
 ELSE
   cmdID := -1; --Set to negative as a flag that the command was found
 END IF;
 -- logic
 RETURN cmdID;
END;
$CMD$
LANGUAGE plpgsql;