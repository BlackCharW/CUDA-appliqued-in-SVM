#include <iostream>
#include <cuda_runtime.h>
#include <device_launch_parameters.h>

using namespace std;

__global__ void vec_add(int *a,int *b)
{
    int i = blockIdx.x;
    a[i] +=b [i];
}

int main()
{
    const int N = 100;
    int *a, *b;
    cudaMallocManaged(&a,N*sizeof(int));
    cudaMallocManaged(&b,N*sizeof(int));

    for(int i = 0;i<N;i++)
    {
        a[i] = i;
        b[i] = 2*i;

    }

    vec_add<<<N,1>>>(a,b);
    cudaDeviceSynchronize();
    for(int i=0;i<N;i++)
    {
        cout << a[i] << endl;
    }
}