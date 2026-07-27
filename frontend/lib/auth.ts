import Keycloak from 'keycloak-js'

const keycloak = new Keycloak({
  url: process.env.NEXT_PUBLIC_KEYCLOAK_URL || 'http://localhost:8180',
  realm: process.env.NEXT_PUBLIC_KEYCLOAK_REALM || 'memguard',
  clientId: process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID || 'memguard-frontend',
})

export async function loginRequired(): Promise<string> {
  const authenticated = await keycloak.init({
    onLoad: 'login-required',
    pkceMethod: 'S256',
    checkLoginIframe: false,
  })

  if (!authenticated || !keycloak.token) {
    throw new Error('Keycloak did not return an access token')
  }
  return keycloak.token
}

export function currentTenantId(): string | undefined {
  const claims = keycloak.tokenParsed as { tenant_id?: string } | undefined
  return claims?.tenant_id
}

export function logout(): Promise<void> {
  return keycloak.logout({ redirectUri: window.location.origin })
}
