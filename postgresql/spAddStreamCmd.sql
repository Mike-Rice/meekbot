CREATE OR REPLACE FUNCTION meekbot.addStreamCmd(streamID bigint, reltn text, cooldown int, cmd_name text, cmd_text text
                                                ,cmd_type text)
RETURNS bigint AS $CMD$
DECLARE
 relationship_cd bigint := 0;
 cmdID bigint := 0;
 second_cd bigint := 0;
 cmd_type_cd bigint := 0;
 active_flag boolean := TRUE;
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

  --Get Command ID
  --Don't care about active indicator because if it exists we want to update the same row
  SELECT
    commands.command_id INTO cmdID
  FROM meekbot.commands
  WHERE stream_id = streamID
    AND command_name = cmd_name;

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

   --CHECK TO SEE IF COMMAND IS ACTIVE.  IF SO SET ID to -1 TO FLAG IT WAS FOUND.  OTHERWISE UPDATE COMMAND
   SELECT commands.active_ind INTO active_flag
   FROM meekbot.commands
   WHERE command_id = cmdID;

   IF active_flag IS TRUE THEN
    cmdID := -1; --Set to negative as a flag that the command was found
   ELSE
    UPDATE meekbot.commands SET stream_reltn_cd = relationship_cd
                               ,updt_dt_tm = now()
                               ,cooldown_dur= cooldown
                               ,cooldown_dur_unit_cd = second_cd
                               ,command_string = cmd_text
                               ,command_type_cd = cmd_type_cd
                               ,active_ind = TRUE
    WHERE command_id = cmdID;
   END IF;

 END IF;
 -- logic
 RETURN cmdID;
END;
$CMD$
LANGUAGE plpgsql;