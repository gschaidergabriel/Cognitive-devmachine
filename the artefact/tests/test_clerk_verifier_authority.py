from clayverse import adapters, clerk_auth


def test_clerk_verifier_has_one_canonical_implementation():
    assert adapters.AuthenticationError is clerk_auth.AuthenticationError
    assert adapters.ClerkConfig is clerk_auth.ClerkConfig
    assert adapters.ClerkTokenVerifier is clerk_auth.ClerkTokenVerifier
