# Smart Money Research state addendum — Phase 607 (2026-11-25 UTC)

- Completed bounded original EDGAR XML reconciliation for six 13F accessions: 2018 Marshall Wace, a clean 2018 control, 2018 OppenheimerFunds, 2026 Dakota Wealth Management, 2026 XXEC, and 2026 Allspring.
- Latest run 45532361067 succeeded; 4/4 offline tests passed; artifact 14985766313 uploaded. All six filing document sets yielded relevant primary-document / information-table XML.
- Source XML confirms that OTHERMANAGER2 sequence numbers are group IDs, not unique manager-row IDs. Allspring's cover page lists five member rows under sequence numbers 1,1,2,2,2; its 3,632 information rows reference groups 1 or 2.
- OppenheimerFunds has 17 member rows across six groups; sequence 1 has 12 members. Its 2,434 numeric information-table references all match a group, but 411 point to a multi-member group.
- The 2018 Marshall Wace sample has sequence groups 1 and 2 but 1,360 source information-table tokens equal 2,811,304; this is an as-filed mismatch.
- The 2026 Dakota sample has groups 1,2,3,8 but 25 source references to absent group 4; this is an as-filed mismatch.
- XXEC's cover page reports zero other included managers, while all 23 information-table rows show literal “XXEC, INC.” in the Other Manager column. Preserve this as raw as-filed text, not as a sequence or two separate identifiers.
- Phase 605's individual-manager graph is not admitted. Replace it with accession → sequence group → member rows; position references attach to groups only.
- No signal, alpha/OOS, bootstrap/LOO or production eligibility is claimed. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; options budget USD 0.
