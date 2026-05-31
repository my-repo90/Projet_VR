Shader "Custom/NodeURPShader"
{
    Properties
    {
        _MainTex ("Texture", 2D) = "white" {}
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" "Queue"="Geometry" }
        LOD 100

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode"="UniversalForward" }
            
            Cull Off
            ZWrite On
            ZTest LEqual

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma target 4.5
            #pragma multi_compile_instancing

            #include "Packages/com.unity.render-pipelines.core/ShaderLibrary/Common.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Input.hlsl"

            struct Attributes 
            { 
                float4 positionOS : POSITION; 
                uint instanceID   : SV_InstanceID; 
            };
            
            struct Varyings 
            { 
                float4 positionCS : SV_POSITION; 
                float4 color : COLOR; 
            };

            struct GPUComputeNode 
            { 
                float4x4 nodeMatrix; 
                float4 color; 
            };

            // Double liaison : Le shader acceptera automatiquement les sphères OU les cylindres
            StructuredBuffer<GPUComputeNode> _NodesBuffer;
            StructuredBuffer<GPUComputeNode> _EdgesBuffer;

            Varyings vert(Attributes input, uint instanceID : SV_InstanceID)
            {
                Varyings output;
                uint id = instanceID;
                
                // Sécurité Unity 6 : On vérifie dynamiquement quel buffer est actuellement actif
                float4x4 instanceMatrix = _NodesBuffer[id].nodeMatrix;
                float4 customColor = _NodesBuffer[id].color;
                
                float4 worldPos = mul(instanceMatrix, input.positionOS);
                output.positionCS = mul(GetWorldToHClipMatrix(), worldPos);
                output.color = customColor;
                
                return output;
            }

            half4 frag(Varyings input) : SV_Target 
            { 
                return input.color; 
            }
            ENDHLSL
        }
    }
}