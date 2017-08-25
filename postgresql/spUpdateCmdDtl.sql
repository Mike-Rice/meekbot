CREATE OR REPLACE FUNCTION meekbot.updateCmdDtl(cmdID bigint, dtl_type text, dtl_txt text, dtl_num real, dtl_seq int)
-- Return a boolean for a success/failure
  RETURNS boolean AS $STATUS$
DECLARE
 dtl_type_cd bigint := 0;
 dtlID bigint := 0;
 detailID bigint := 0;
 detail_update_flg boolean := false;
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
                                     ,detail_text
                                     ,detail_num
                                     ,seq
                                     ,create_dt_tm)
   VALUES (cmdID,'TEMP', dtl_type_cd, dtl_txt, dtl_num,dtl_seq,now())
   RETURNING command_detail.command_detail_id INTO dtlID;
 ELSE
   dtlID := detailID;
   --Set active indicator and reset values
   UPDATE meekbot.command_detail SET detail_type_cd = dtl_type_cd
                                  , detail_name = 'TEMP'
                                  , detail_text = dtl_txt
                                  , detail_num = dtl_num
                                  , active_ind = TRUE
                                  , updt_dt_tm = now()
   WHERE command_detail_id = detailID;
 END IF;

 IF dtlID IS NOT NULL THEN
   detail_update_flg = TRUE ;
 END IF;
 -- logic
 RETURN detail_update_flg;
END;
$STATUS$
LANGUAGE plpgsql;