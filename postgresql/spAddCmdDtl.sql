CREATE OR REPLACE FUNCTION meekbot.addCmdDtl(cmdID bigint, dtl_type text, dtl_seq int)
RETURNS bigint AS $DTL$
DECLARE
 dtl_type_cd bigint := 0;
 dtlID bigint := 0;
 detailID bigint := 0;
BEGIN

  --Get detail type code
SELECT
  code_value.code_value INTO dtl_type_cd
FROM
  meekbot.code_value
WHERE code_set = 4
  AND display_key = dtl_type
  AND active_ind = TRUE;

  --Check to see if there is already a detail for this command for this sequence
  --Don't care about active indicator because if it exists we'll be setting it to active anyway
 SELECT
   command_detail.command_detail_id INTO detailID
 FROM meekbot.command_detail
 WHERE command_id = cmdID
   AND seq = dtl_seq;

 --Add logic to see if command already exists and return a negative value if so
 IF detailID IS NULL THEN
   INSERT INTO meekbot.command_detail(command_id
                                     ,detail_name
                                     ,detail_type_cd
                                     ,seq
                              , create_dt_tm)
   VALUES (cmdID,'TEMP', dtl_type_cd, dtl_seq,now())
   RETURNING command_detail.command_detail_id INTO dtlID;
 ELSE
   dtlID := detailID;
   --Set active indicator and reset values
   UPDATE meekbot.command_detail SET detail_type_cd = dtl_type_cd
                                  , detail_name = 'TEMP'
                                  , detail_text = ''
                                  , detail_num = 0
                                  , active_ind = TRUE WHERE command_detail_id = detailID;
 END IF;
 -- logic
 RETURN dtlID;
END;
$DTL$
LANGUAGE plpgsql;