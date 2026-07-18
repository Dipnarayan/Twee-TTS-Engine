@echo off
title Twee

:: arr.bat -- simulates creation of an array with script arguments
setlocal enabledelayedexpansion

set args=%*
set arr.length=0

rem delayed expansion of %args% here to prevent if statement from freaking out
rem if quotation marks or spaces are encountered
::if #!args!==# goto :usage

rem ###############
rem construct array
rem ###############

rem surround each argument with quotation marks and loop through them
rem 1 "2 3" 4 becomes "1" ""2" "3"" "4" (keeping 2 and 3 grouped)
for %%I in ("%args: =" "%") do (

    rem Pop quiz, hotshot.  Why did I not just use `set arr[!arr.length!]=%%~I`
    rem to strip the quotation marks?  Try it and see what happens.
    set val=%%I
    set arr[!arr.length!]=!val:"=!

    rem incrememt %array.length%
    set /a arr.length=!arr.length! + 1
)

rem ##############
rem retrieve array
rem ##############

::echo arr[] has a length of %arr.length%.

rem arr.Ubound is the highest index in the array.  For instance, if the array
rem has 4 elements, then !arr[%arr.Ubound%]! refers to %arr[3]%.
set /a arr.Ubound=%arr.length% - 1
for /L %%I in (0, 1, %arr.Ubound%) do (

    rem To retrieve an array element, expand the inner variable immediately
    rem while delaying expansion of the outer variable.
    rem echo arr[%%I] = !arr[%%I]!
)

::goto :EOF

::usage
::exit
::echo Usage: %~nx0 [arg [arg [arg]]] etc.

call twee.exe %*