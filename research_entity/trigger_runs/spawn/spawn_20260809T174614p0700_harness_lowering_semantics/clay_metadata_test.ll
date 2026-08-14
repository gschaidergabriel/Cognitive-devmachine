define i32 @f() {
entry:
  %y = add i32 1, 1, !clay.auth !0
  ret i32 %y
}
!0 = !{!"epistemic:CONFLICT;prov:ev1+ev2"}
