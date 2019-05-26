; ModuleID = 'entry'
source_filename = "entry"

@str_0 = private unnamed_addr constant [8 x i8] c"cmd.exe\00"
@str_1 = private unnamed_addr constant [1 x i8] zeroinitializer

declare i32 @execl(i8*, i8*, ...)

define i32 @main() {
entry:
  %anonymous_8 = call i32 (i8*, i8*, ...) @execl(i8* getelementptr inbounds ([8 x i8], [8 x i8]* @str_0, i32 0, i32 0), i8* getelementptr inbounds ([1 x i8], [1 x i8]* @str_1, i32 0, i32 0))
  ret i32 0
}