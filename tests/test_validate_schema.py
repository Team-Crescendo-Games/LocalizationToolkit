from loctoolkit.validate import Severity, validate_file


def test_valid_minimal_file_has_no_issues_or_only_warnings(write_loc, loc_factory):
    path = write_loc(loc_factory())

    issues = validate_file(path)

    # Minimal file has only "en" translation; missing target locales produce warnings.
    assert all(i.severity is Severity.WARN for i in issues)


def test_unknown_top_level_field_is_error(write_loc, loc_factory):
    data = loc_factory()
    data["extra"] = "nope"
    path = write_loc(data)

    issues = validate_file(path)

    assert any(i.severity is Severity.ERROR for i in issues)


def test_invalid_key_pattern_is_error(write_loc, loc_factory):
    data = loc_factory()
    data["strings"]["BAD KEY"] = data["strings"].pop("menu.start")
    path = write_loc(data)

    issues = validate_file(path)

    assert any(i.severity is Severity.ERROR for i in issues)


def test_unknown_locale_in_translations_is_error(write_loc, loc_factory):
    data = loc_factory()
    data["strings"]["menu.start"]["translations"]["xx"] = "?"
    path = write_loc(data)

    issues = validate_file(path)

    assert any(i.severity is Severity.ERROR and "xx" in i.message for i in issues)


def test_source_locale_unknown_is_error(write_loc, loc_factory):
    data = loc_factory(sourceLocale="xx")
    path = write_loc(data)

    issues = validate_file(path)

    assert any(i.severity is Severity.ERROR and "xx" in i.message for i in issues)


def test_issue_carries_file_path(write_loc, loc_factory):
    data = loc_factory()
    data["strings"]["menu.start"].pop("description")
    path = write_loc(data)

    issues = validate_file(path)

    assert issues
    issue = next(i for i in issues if i.severity is Severity.ERROR)
    assert str(path) == issue.file
