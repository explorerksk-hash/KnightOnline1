-- Maden gorselleri v2: CZ merkezine cevher damari nesneleri
-- Merkez 1014.9, 992.7  |  tasarim: docs/design/maden.md
--
-- sPid degerleri Data/NPC_Looks.tbl'den dogrulandi. Model begenilmezse
-- asagidaki sPid'i degistirip SQL'i tekrar calistirmak yeterli:
--   30090 npc_dong_gold      altin cevher yigini
--   30094 el_dong_gold       altin cevher (El Morad)
--   30091 obj_ka_crystal01   kristal (Karus)
--   30092 obj_el_crystal02   kristal (El Morad)
--   24000 obj_kaa_kugglin_stone  kaya
--   30020 obj_war_clanstone      klan tasi
SET NOCOUNT ON;

DELETE FROM dbo.K_NPC    WHERE sSid   IN (9100, 9101);
DELETE FROM dbo.K_NPCPOS WHERE ZoneID = 201 AND NpcID IN (9100, 9101);

-- byType=46 (NPC_GENERIC): tamamen dekor, vurulmaz ve tiklanmaz.
INSERT INTO dbo.K_NPC (sSid, strName, sPid,sSize,iWeapon1,iWeapon2,byGroup,byActType,byType,byFamily,byRank,byTitle,iSellingGroup,sLevel,iExp,iLoyalty,iHpPoint,sMpPoint,sAtk,sAc,sHitRate,sEvadeRate,sDamage,sAttackDelay,bySpeed1,bySpeed2,sStandtime,iMagic1,iMagic2,iMagic3,sFireR,sColdR,sLightningR,sMagicR,sDiseaseR,sPoisonR,sLightR,sBulk,byAttackRange,bySearchRange,byTracingRange,iMoney,sItem,byDirectAttack,byMagicAttack,byMoneyType)
  VALUES (9100, N'Cevher Damari', 30090, 110, 0,0,1,0,46,1,1,1,0,60,0,0,10000,0,0,360,194,194,0,1000,0,0,1000,0,0,0,250,250,250,250,250,250,250,100,5,5,5,0,0,0,0,0);  -- npc_dong_gold
INSERT INTO dbo.K_NPC (sSid, strName, sPid,sSize,iWeapon1,iWeapon2,byGroup,byActType,byType,byFamily,byRank,byTitle,iSellingGroup,sLevel,iExp,iLoyalty,iHpPoint,sMpPoint,sAtk,sAc,sHitRate,sEvadeRate,sDamage,sAttackDelay,bySpeed1,bySpeed2,sStandtime,iMagic1,iMagic2,iMagic3,sFireR,sColdR,sLightningR,sMagicR,sDiseaseR,sPoisonR,sLightR,sBulk,byAttackRange,bySearchRange,byTracingRange,iMoney,sItem,byDirectAttack,byMagicAttack,byMoneyType)
  VALUES (9101, N'Buyuk Cevher Damari', 30091, 170, 0,0,1,0,46,1,1,1,0,60,0,0,10000,0,0,360,194,194,0,1000,0,0,1000,0,0,0,250,250,250,250,250,250,250,100,5,5,5,0,0,0,0,0);  -- obj_ka_crystal01

INSERT INTO dbo.K_NPCPOS (ZoneID,NpcID,ActType,RegenType,DungeonFamily,SpecialType,TrapNumber,LeftX,TopZ,RightX,BottomZ,LimitMinX,LimitMinZ,LimitMaxX,LimitMaxZ,NumNPC,RegTime,byDirection,DotCnt) VALUES (201,9101,100,0,0,0,0,1015,994,1016,993,1015,993,1016,994,1,60,0,0);  -- merkez-kristal
INSERT INTO dbo.K_NPCPOS (ZoneID,NpcID,ActType,RegenType,DungeonFamily,SpecialType,TrapNumber,LeftX,TopZ,RightX,BottomZ,LimitMinX,LimitMinZ,LimitMaxX,LimitMaxZ,NumNPC,RegTime,byDirection,DotCnt) VALUES (201,9100,100,0,0,0,0,1049,994,1050,993,1049,993,1050,994,1,60,0,0);  -- damar-34
INSERT INTO dbo.K_NPCPOS (ZoneID,NpcID,ActType,RegenType,DungeonFamily,SpecialType,TrapNumber,LeftX,TopZ,RightX,BottomZ,LimitMinX,LimitMinZ,LimitMaxX,LimitMaxZ,NumNPC,RegTime,byDirection,DotCnt) VALUES (201,9100,100,0,0,0,0,1039,1018,1040,1017,1039,1017,1040,1018,1,60,0,0);  -- damar-34
INSERT INTO dbo.K_NPCPOS (ZoneID,NpcID,ActType,RegenType,DungeonFamily,SpecialType,TrapNumber,LeftX,TopZ,RightX,BottomZ,LimitMinX,LimitMinZ,LimitMaxX,LimitMaxZ,NumNPC,RegTime,byDirection,DotCnt) VALUES (201,9100,100,0,0,0,0,1015,1028,1016,1027,1015,1027,1016,1028,1,60,0,0);  -- damar-34
INSERT INTO dbo.K_NPCPOS (ZoneID,NpcID,ActType,RegenType,DungeonFamily,SpecialType,TrapNumber,LeftX,TopZ,RightX,BottomZ,LimitMinX,LimitMinZ,LimitMaxX,LimitMaxZ,NumNPC,RegTime,byDirection,DotCnt) VALUES (201,9100,100,0,0,0,0,991,1018,992,1017,991,1017,992,1018,1,60,0,0);  -- damar-34
INSERT INTO dbo.K_NPCPOS (ZoneID,NpcID,ActType,RegenType,DungeonFamily,SpecialType,TrapNumber,LeftX,TopZ,RightX,BottomZ,LimitMinX,LimitMinZ,LimitMaxX,LimitMaxZ,NumNPC,RegTime,byDirection,DotCnt) VALUES (201,9100,100,0,0,0,0,981,994,982,993,981,993,982,994,1,60,0,0);  -- damar-34
INSERT INTO dbo.K_NPCPOS (ZoneID,NpcID,ActType,RegenType,DungeonFamily,SpecialType,TrapNumber,LeftX,TopZ,RightX,BottomZ,LimitMinX,LimitMinZ,LimitMaxX,LimitMaxZ,NumNPC,RegTime,byDirection,DotCnt) VALUES (201,9100,100,0,0,0,0,991,970,992,969,991,969,992,970,1,60,0,0);  -- damar-34
INSERT INTO dbo.K_NPCPOS (ZoneID,NpcID,ActType,RegenType,DungeonFamily,SpecialType,TrapNumber,LeftX,TopZ,RightX,BottomZ,LimitMinX,LimitMinZ,LimitMaxX,LimitMaxZ,NumNPC,RegTime,byDirection,DotCnt) VALUES (201,9100,100,0,0,0,0,1015,960,1016,959,1015,959,1016,960,1,60,0,0);  -- damar-34
INSERT INTO dbo.K_NPCPOS (ZoneID,NpcID,ActType,RegenType,DungeonFamily,SpecialType,TrapNumber,LeftX,TopZ,RightX,BottomZ,LimitMinX,LimitMinZ,LimitMaxX,LimitMaxZ,NumNPC,RegTime,byDirection,DotCnt) VALUES (201,9100,100,0,0,0,0,1039,970,1040,969,1039,969,1040,970,1,60,0,0);  -- damar-34
INSERT INTO dbo.K_NPCPOS (ZoneID,NpcID,ActType,RegenType,DungeonFamily,SpecialType,TrapNumber,LeftX,TopZ,RightX,BottomZ,LimitMinX,LimitMinZ,LimitMaxX,LimitMaxZ,NumNPC,RegTime,byDirection,DotCnt) VALUES (201,9100,100,0,0,0,0,1076,1019,1077,1018,1076,1018,1077,1019,1,60,0,0);  -- damar-66
INSERT INTO dbo.K_NPCPOS (ZoneID,NpcID,ActType,RegenType,DungeonFamily,SpecialType,TrapNumber,LeftX,TopZ,RightX,BottomZ,LimitMinX,LimitMinZ,LimitMaxX,LimitMaxZ,NumNPC,RegTime,byDirection,DotCnt) VALUES (201,9100,100,0,0,0,0,1040,1055,1041,1054,1040,1054,1041,1055,1,60,0,0);  -- damar-66
INSERT INTO dbo.K_NPCPOS (ZoneID,NpcID,ActType,RegenType,DungeonFamily,SpecialType,TrapNumber,LeftX,TopZ,RightX,BottomZ,LimitMinX,LimitMinZ,LimitMaxX,LimitMaxZ,NumNPC,RegTime,byDirection,DotCnt) VALUES (201,9100,100,0,0,0,0,989,1054,990,1053,989,1053,990,1054,1,60,0,0);  -- damar-66
INSERT INTO dbo.K_NPCPOS (ZoneID,NpcID,ActType,RegenType,DungeonFamily,SpecialType,TrapNumber,LeftX,TopZ,RightX,BottomZ,LimitMinX,LimitMinZ,LimitMaxX,LimitMaxZ,NumNPC,RegTime,byDirection,DotCnt) VALUES (201,9100,100,0,0,0,0,954,1019,955,1018,954,1018,955,1019,1,60,0,0);  -- damar-66
INSERT INTO dbo.K_NPCPOS (ZoneID,NpcID,ActType,RegenType,DungeonFamily,SpecialType,TrapNumber,LeftX,TopZ,RightX,BottomZ,LimitMinX,LimitMinZ,LimitMaxX,LimitMaxZ,NumNPC,RegTime,byDirection,DotCnt) VALUES (201,9100,100,0,0,0,0,954,968,955,967,954,967,955,968,1,60,0,0);  -- damar-66
INSERT INTO dbo.K_NPCPOS (ZoneID,NpcID,ActType,RegenType,DungeonFamily,SpecialType,TrapNumber,LeftX,TopZ,RightX,BottomZ,LimitMinX,LimitMinZ,LimitMaxX,LimitMaxZ,NumNPC,RegTime,byDirection,DotCnt) VALUES (201,9100,100,0,0,0,0,990,933,991,932,990,932,991,933,1,60,0,0);  -- damar-66
INSERT INTO dbo.K_NPCPOS (ZoneID,NpcID,ActType,RegenType,DungeonFamily,SpecialType,TrapNumber,LeftX,TopZ,RightX,BottomZ,LimitMinX,LimitMinZ,LimitMaxX,LimitMaxZ,NumNPC,RegTime,byDirection,DotCnt) VALUES (201,9100,100,0,0,0,0,1041,933,1042,932,1041,932,1042,933,1,60,0,0);  -- damar-66
INSERT INTO dbo.K_NPCPOS (ZoneID,NpcID,ActType,RegenType,DungeonFamily,SpecialType,TrapNumber,LeftX,TopZ,RightX,BottomZ,LimitMinX,LimitMinZ,LimitMaxX,LimitMaxZ,NumNPC,RegTime,byDirection,DotCnt) VALUES (201,9100,100,0,0,0,0,1076,969,1077,968,1076,968,1077,969,1,60,0,0);  -- damar-66

SELECT COUNT(*) AS yerlestirilen FROM dbo.K_NPCPOS WHERE ZoneID=201 AND NpcID IN (9100,9101);
