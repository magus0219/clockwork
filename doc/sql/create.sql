SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL,ALLOW_INVALID_DATES';


-- -----------------------------------------------------
-- Table `CW_JOB`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `CW_JOB` ;

CREATE TABLE IF NOT EXISTS `CW_JOB` (
  `RecordID` BIGINT NOT NULL AUTO_INCREMENT COMMENT '自增长ID',
  `Name` VARCHAR(64) NOT NULL COMMENT '名称',
  `TimePattern` VARCHAR(32) NOT NULL COMMENT '触发时间模式',
  `SSHHost` VARCHAR(64) NULL COMMENT '执行该命令的远程机器地址',
  `Command` TEXT NOT NULL COMMENT '操作命令',
  `Retry` TINYINT NOT NULL COMMENT '重试次数',
  `Type` TINYINT NOT NULL COMMENT '1-简单任务 2-复杂任务',
  `EnableFlag` TINYINT(1) NOT NULL COMMENT '是否启用',
  `Description` TEXT NULL COMMENT '描述',
  `MTime` TIMESTAMP NOT NULL COMMENT '修改时间',
  PRIMARY KEY (`RecordID`))
ENGINE = InnoDB
COMMENT = '工作';


-- -----------------------------------------------------
-- Table `CW_JOB_DEPENDENCE`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `CW_JOB_DEPENDENCE` ;

CREATE TABLE IF NOT EXISTS `CW_JOB_DEPENDENCE` (
  `RecordID` BIGINT NOT NULL AUTO_INCREMENT COMMENT '自增长ID',
  `JobID` BIGINT NOT NULL COMMENT '工作id',
  `JobID_Depend` BIGINT NOT NULL COMMENT '依赖工作id',
  `JobID_Complex` BIGINT NOT NULL COMMENT '复杂工作id',
  `DeltaDay` INT NOT NULL DEFAULT 0 COMMENT '提前量天',
  `DeltaHour` INT NOT NULL DEFAULT 0 COMMENT '提前量小时',
  `DeltaMinute` INT NOT NULL DEFAULT 0 COMMENT '提前量分钟',
  `MTime` TIMESTAMP NOT NULL COMMENT '修改时间',
  PRIMARY KEY (`RecordID`),
  CONSTRAINT `fk_CW_JOB_DEPENDENCE_CW_JOB`
    FOREIGN KEY (`JobID`)
    REFERENCES `CW_JOB` (`RecordID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_CW_JOB_DEPENDENCE_CW_JOB1`
    FOREIGN KEY (`JobID_Depend`)
    REFERENCES `CW_JOB` (`RecordID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
COMMENT = '工作依赖关系';

CREATE INDEX `fk_CW_JOB_DEPENDENCE_CW_JOB_idx` ON `CW_JOB_DEPENDENCE` (`JobID` ASC);

CREATE INDEX `fk_CW_JOB_DEPENDENCE_CW_JOB1_idx` ON `CW_JOB_DEPENDENCE` (`JobID_Depend` ASC);

CREATE UNIQUE INDEX `IDX_PK` ON `CW_JOB_DEPENDENCE` (`JobID` ASC, `JobID_Depend` ASC);


-- -----------------------------------------------------
-- Table `CW_TASK_STATUS`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `CW_TASK_STATUS` ;

CREATE TABLE IF NOT EXISTS `CW_TASK_STATUS` (
  `RecordID` BIGINT NOT NULL AUTO_INCREMENT COMMENT '自增长ID',
  `StatusID` TINYINT NOT NULL COMMENT '状态id',
  `Description` VARCHAR(32) NOT NULL COMMENT '描述',
  `MTime` TIMESTAMP NOT NULL COMMENT '修改时间',
  PRIMARY KEY (`RecordID`))
ENGINE = InnoDB
COMMENT = '任务状态';

CREATE UNIQUE INDEX `IDX_PK` ON `CW_TASK_STATUS` (`StatusID` ASC);


-- -----------------------------------------------------
-- Table `CW_TASK`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `CW_TASK` ;

CREATE TABLE IF NOT EXISTS `CW_TASK` (
  `RecordID` BIGINT NOT NULL AUTO_INCREMENT COMMENT '自增长ID',
  `TaskID` VARCHAR(128) NOT NULL COMMENT '任务id',
  `TaskID_Cmplx` VARCHAR(128) NULL,
  `JobID` BIGINT NOT NULL COMMENT '工作id',
  `ExecuteTime` DATETIME NOT NULL COMMENT '执行时间',
  `EndTime` DATETIME NULL COMMENT '结束时间',
  `Retry` TINYINT NOT NULL COMMENT '重试次数',
  `Command` TEXT NOT NULL COMMENT '操作命令',
  `Status` TINYINT NOT NULL COMMENT '状态',
  `Description` TEXT NULL COMMENT '描述',
  `MTime` TIMESTAMP NOT NULL COMMENT '修改时间',
  PRIMARY KEY (`RecordID`),
  CONSTRAINT `fk_CW_TASK_CW_JOB1`
    FOREIGN KEY (`JobID`)
    REFERENCES `CW_JOB` (`RecordID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_CW_TASK_CW_TASK_STATUS1`
    FOREIGN KEY (`Status`)
    REFERENCES `CW_TASK_STATUS` (`StatusID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
COMMENT = '任务';

CREATE UNIQUE INDEX `IDX_PK` ON `CW_TASK` (`TaskID` ASC);

CREATE INDEX `IDX_JOBID` ON `CW_TASK` (`JobID` ASC);

CREATE INDEX `IDX_EXETIME` ON `CW_TASK` (`ExecuteTime` ASC);

CREATE INDEX `fk_CW_TASK_CW_JOB1_idx` ON `CW_TASK` (`JobID` ASC);

CREATE INDEX `fk_CW_TASK_CW_TASK_STATUS1_idx` ON `CW_TASK` (`Status` ASC);


-- -----------------------------------------------------
-- Table `CW_JOB_INCLUSION`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `CW_JOB_INCLUSION` ;

CREATE TABLE IF NOT EXISTS `CW_JOB_INCLUSION` (
  `RecordID` BIGINT NOT NULL AUTO_INCREMENT COMMENT '自增长ID',
  `JobID` BIGINT NOT NULL COMMENT '工作id',
  `JobID_Inclusion` BIGINT NOT NULL COMMENT '依赖工作id',
  `MTime` TIMESTAMP NOT NULL COMMENT '修改时间',
  PRIMARY KEY (`RecordID`),
  CONSTRAINT `fk_CW_JOB_DEPENDENCE_CW_JOB0`
    FOREIGN KEY (`JobID`)
    REFERENCES `CW_JOB` (`RecordID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_CW_JOB_DEPENDENCE_CW_JOB10`
    FOREIGN KEY (`JobID_Inclusion`)
    REFERENCES `CW_JOB` (`RecordID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
COMMENT = '复杂工作包含关系';

CREATE INDEX `fk_CW_JOB_DEPENDENCE_CW_JOB_idx` ON `CW_JOB_INCLUSION` (`JobID` ASC);

CREATE INDEX `fk_CW_JOB_DEPENDENCE_CW_JOB1_idx` ON `CW_JOB_INCLUSION` (`JobID_Inclusion` ASC);

CREATE UNIQUE INDEX `IDX_PK` ON `CW_JOB_INCLUSION` (`JobID` ASC, `JobID_Inclusion` ASC);


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;

-- -----------------------------------------------------
-- Data for table `CW_TASK_STATUS`
-- -----------------------------------------------------
START TRANSACTION;
INSERT INTO `CW_TASK_STATUS` (`RecordID`, `StatusID`, `Description`, `MTime`) VALUES (1, 10, '未执行', NULL);
INSERT INTO `CW_TASK_STATUS` (`RecordID`, `StatusID`, `Description`, `MTime`) VALUES (2, 20, '正在执行', NULL);
INSERT INTO `CW_TASK_STATUS` (`RecordID`, `StatusID`, `Description`, `MTime`) VALUES (3, 30, '执行成功', NULL);
INSERT INTO `CW_TASK_STATUS` (`RecordID`, `StatusID`, `Description`, `MTime`) VALUES (4, 40, '执行失败', NULL);
INSERT INTO `CW_TASK_STATUS` (`RecordID`, `StatusID`, `Description`, `MTime`) VALUES (NULL, 50, '执行取消', NULL);

COMMIT;

