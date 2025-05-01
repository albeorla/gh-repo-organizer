"""Simple test for execute_actions parameter checking."""


def test_execute_actions_signature():
    """Test that the execute_actions function accepts a username parameter.

    This test doesn't actually run the function, just inspects its signature.
    """
    # Import the function directly to check its signature
    import inspect

    from repo_organizer.cli.commands import execute_actions

    # Get the signature of the function
    signature = inspect.signature(execute_actions)

    # Check that 'username' is in the parameters
    assert "username" in signature.parameters

    # Check that username parameter has the right default (None)
    assert signature.parameters["username"].default is None
