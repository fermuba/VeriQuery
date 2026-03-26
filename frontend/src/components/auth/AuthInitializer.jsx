/**
 * Auth Integration - Inicializa el token para llamadas API
 * 
 * Este componente configura la función getAccessToken en el módulo de API
 */

import { useEffect } from 'react'
import { useAuth } from '../../auth'
import { setGetAccessTokenFunction } from '../../config/api'

/**
 * AuthInitializer Component
 * 
 * Debe estar dentro de AuthProvider para obtener el contexto de autenticación
 * Configura la API para usar el token automáticamente
 */
export function AuthInitializer({ children }) {
  const { getAccessToken } = useAuth()

  useEffect(() => {
    // Pasar la función getAccessToken al módulo de API
    setGetAccessTokenFunction(getAccessToken)
  }, [getAccessToken])

  return children
}

export default AuthInitializer
